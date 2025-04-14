#!/usr/bin/env python3

import asyncio
import math
import moteus
from moteus import Register
import time
from collections import namedtuple

"""

    Script to collect data from moteus controller to compare agianst simulated controller

    IMPORTANT: Make sure motor and spin contiously freely in either direction!

    Helpful shortcuts:

    python3 -m moteus_gui.tview --devices=1 --fdcanusb /dev/serial/by-id/usb-mjbots_fdcanusb_1533F30D-if00

    Notes:
    - Free spining motors have lower interia and may become unstable if kd is to high

"""

Command = namedtuple('Command', ['pos', 'vel', 'ff', 'kp', 'kd', 'max_t'])

async def main():

    # Find transport path with
    # cd /dev/serial/by-id && ls
    # example: 
    # transport_path = "/dev/serial/by-id/usb-mjbots_fdcanusb_1533F30D-if00"
    # If none, then will autodetect

    transport_path = None
    servo_ids = [1] # fill with the CAN ID of your servos

    # Set with the constants of the controller
    _kp = 1
    _kd = 1
    _ki = 1
    _i_limit = 1

    transport = moteus.Fdcanusb(path=transport_path)

    pid_info_query = moteus.QueryResolution()
    
    # Check the register for other fields you may want to add
    pid_info_query._extra = {
        # Register.COMMAND_POSITION: moteus.F32,
        # Register.COMMAND_VELOCITY: moteus.F32,
        # Register.COMMAND_FEEDFORWARD_TORQUE: moteus.F32,
        # Register.COMMAND_KP_SCALE: moteus.F32,
        # Register.COMMAND_KD_SCALE: moteus.F32,
        # Register.COMMAND_POSITION_MAX_TORQUE: moteus.F32,
        # Register.COMMAND_VELOCITY_LIMIT: moteus.F32,
        # Register.COMMAND_ACCEL_LIMIT: moteus.F32,
        # Register.COMMAND_ILIMIT_SCALE: moteus.F32,

        Register.POSITION_KP: moteus.F32,
        Register.POSITION_KI: moteus.F32,
        Register.POSITION_KD: moteus.F32,
        Register.POSITION_FEEDFORWARD: moteus.F32,
        Register.POSITION_COMMAND: moteus.F32,

        # Register.CONTROL_POSITION: moteus.F32,
        # Register.CONTROL_VELOCITY: moteus.F32,
        # Register.CONTROL_TORQUE: moteus.F32,
        # Register.POSITION_ERROR: moteus.F32,
        # Register.VELOCITY_ERROR: moteus.F32,
        # Register.TORQUE_ERROR: moteus.F32,
    }
    
    servos = {
        servo_id: moteus.Controller(id=servo_id, query_resolution=pid_info_query)
        for servo_id in servo_ids
    }

    await transport.cycle([x.make_stop() for x in servos.values()])


    print("Starting Control")

    # a variety of commands to generate diverse behaviour
    test_cases = [
        'd pos nan 0 nan p0 d0 f0.01', # positon control 
        'd pos 0 0 1 p0 d0 f0.01', # torque control
        'd pos nan 0 nan p0 d0 f0.01', # torque control
        'd pos nan 0 nan p0 d0 f0.01', # torque control
    ]


    def str_command(cmd_str):
        parts = cmd_str.split()

        def to_float_or_nan(val):
            return float(val) if val.lower() != "nan" else math.nan

        pos = to_float_or_nan(parts[2])
        vel = to_float_or_nan(parts[3])
        max_t = to_float_or_nan(parts[4])
        kp = float(parts[5][1:])  # remove 'p' prefix
        kd = float(parts[6][1:])  # remove 'd' prefix
        ff = float(parts[7][1:])  # remove 'f' prefix

        return Command(pos, vel, ff, kp, kd, max_t)

    print("All Commands:")
    for cmd in test_cases:
        print(str_command(cmd))


    cmd_index = 0
    curr_cmd =  str_command(test_cases[cmd_index])

    last_time = time.time()  # Track the last time the velocity was flipped

    while True:
        current_time = time.time()

        if current_time - last_time > 2:
            last_time = current_time
            cmd_index += 1 

            if cmd_index >= len(test_cases):
                print("Done all commmands")
                break
            curr_cmd =  str_command(test_cases[cmd_index])
            print("Using New Command: ", curr_cmd)


        commands = [
            servos[1].make_position(
                    position=curr_cmd.pos,
                    velocity=curr_cmd.vel,
                    feedforward_torque=curr_cmd.ff,
                    kp_scale=curr_cmd.kp,
                    kd_scale=curr_cmd.kd,
                    maximum_torque=curr_cmd.max_t,
                    watchdog_timeout=1.0, # slow down a bit
                    # velocity_limit=None,
                    # accel_limit=None,
                    query=True)
        ]

        results = await transport.cycle(commands)
        for result in results:
            print(f"Servo ID {result.arbitration_id}:")
            print(result)
            for reg, val in result.values.items():
                
                print(f"  {reg}: {val}")
            print("---")
        # print(", ".join(
        #     f"({result.arbitration_id} " +
        #     f"{result.values[moteus.Register.POSITION]} " +
        #     f"{result.values[moteus.Register.VELOCITY]})"
        #     for result in results))

        # log files to text file to compare with afterwards
        await asyncio.sleep(0.25)

if __name__ == '__main__':
    asyncio.run(main())
