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

async def main():

    # --------- EDIT THIS INFO -------------

    # Find transport path with
    # cd /dev/serial/by-id && ls
    # example: 
    # transport_path = "/dev/serial/by-id/usb-mjbots_fdcanusb_1533F30D-if00"
    # If None, then will autodetect

    transport_path = None
    servo_id = 1 # fill with the CAN ID of your servos

    # Set with the constants of the controller
    _kp = 1
    _kd = 1
    _ki = 1
    _i_limit = 1

    # ------------------------------

    transport = moteus.Fdcanusb(path=transport_path)

    pid_info_query = moteus.QueryResolution()
    pid_info_query.mode = moteus.IGNORE
    pid_info_query.position = moteus.F32
    pid_info_query.velocity = moteus.F32
    pid_info_query.torque = moteus.F32
    pid_info_query.voltage = moteus.IGNORE
    pid_info_query.temperature = moteus.IGNORE
    pid_info_query.fault = moteus.IGNORE

    # Check the register for other fields you may want to add
    pid_info_query._extra = {
        Register.CONTROL_POSITION: moteus.F32,
        Register.CONTROL_VELOCITY: moteus.F32,
        Register.CONTROL_TORQUE: moteus.F32,
        Register.POSITION_ERROR: moteus.F32,
        Register.VELOCITY_ERROR: moteus.F32,
        Register.TORQUE_ERROR: moteus.F32,
        Register.POSITION_KP: moteus.F32,
        Register.POSITION_KI: moteus.F32,
        Register.POSITION_KD: moteus.F32,
        Register.POSITION_FEEDFORWARD: moteus.F32,
        Register.POSITION_COMMAND: moteus.F32,
    }
    
    

    servo = moteus.Controller(id=servo_id, query_resolution=pid_info_query)
 

    await transport.cycle([servo.make_stop()])

    # a variety of commands to generate diverse behaviour
    test_cases = [
        'd pos 1 0 nan p1 d1 f0', # positon control 
        'd pos -1 0 nan p1 d1 f0', # positon control 

        'd pos nan -1 nan p1 d1 f0', # velocity control 
        'd pos nan 1 nan p1 d1 f0', # velocity control # TODO may need to recapture.

        # 'd pos 1 1 nan p1 d1 f0', # hybrid
        # 'd pos -1 -1 nan p1 d1 f0', # hybrid
        # 'd pos 1 1 nan p1 d1 f1', # hybrid w/ ff
        # 'd pos -1 -1 nan p1 d1 f-1', # hybrid w/ ff
        # 'd pos 1 1 nan p1 d1 f-1', # hybrid w/ ff
        # 'd pos -1 -1 0.5 p1 d1 f-1', # hybrid w/ ff & max_torque
        # 'd pos 1 1 0.5 p1 d1 f1', # hybrid w/ ff & max_torque
        # 'd pos 1 1 0.5 p0.5 d0.5 f1', # hybrid w/ ff & max_torque & scaling

        # 'd pos 0 0 nan p0.5 d0.5 f0', # scaling kp/kd
        # 'd pos 1 1 nan p1 d1 f0', # scaling kp/kd
        # 'd pos 1 1 nan p0 d0 f0', # scaling kp/kd

        # 'd pos -1 -1 nan p0 d0 f-1', # torque control
        # 'd pos nan 0 nan p0 d0 f1', # torque control
        # 'd pos nan 0 nan p0 d0 f-1', # torque control

    ]

    Command = namedtuple('Command', ['pos', 'vel', 'ff', 'kp', 'kd', 'max_t'])

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


    log_file = open("pid_log.txt", "w")
    log_file.write("kp,kd,ki,i_limit\n")
    log_file.write(f"{_kp},{_kd},{_ki},{_i_limit}\n")
    log_file.write("cmd_index,pos,vel,ff,kp,kd,max_t,servo_id,register,value\n")


    cmd_index = 0
    curr_cmd =  str_command(test_cases[cmd_index])
    last_time = time.time()  

    print("Starting Control")

    while True:
        current_time = time.time()

        if current_time - last_time > 2:
            
            # reset so not, later commands are not influence by previous ones
            await transport.cycle([servo.make_stop()])
            await transport.cycle([servo.make_recapture_position_velocity()])

            last_time = current_time
            cmd_index += 1 

            if cmd_index >= len(test_cases):
                print("Done all commmands")
                break

            curr_cmd =  str_command(test_cases[cmd_index])
            print("Using New Command: ", curr_cmd)


        commands = [
            servo.make_position(
                    position=curr_cmd.pos,
                    velocity=curr_cmd.vel,
                    feedforward_torque=curr_cmd.ff,
                    kp_scale=curr_cmd.kp,
                    kd_scale=curr_cmd.kd,
                    maximum_torque=curr_cmd.max_t,
                    watchdog_timeout=1.0, # allows you to loop & log slower
                    query=True)
        ]

        results = await transport.cycle(commands)

        v = results[0].values


            # for reg, val in result.values.items():
                # print(f"  {reg}: {val}")

        # log_file.write("cmd_index,pos,vel,max_t,ff,kp,kd,KP,\n")

        log_file.write(f"{cmd_index},{curr_cmd.pos},{curr_cmd.vel},{curr_cmd.max_t},{curr_cmd.kp},{curr_cmd.kd},{curr_cmd.ff},\n")

        print(f"{v[Register.CONTROL_POSITION]} - {v[Register.POSITION]} = {v[Register.POSITION_ERROR]}")
        # print(f"{v[Register.CONTROL_VELOCITY]} - {v[Register.VELOCITY]} = {v[Register.VELOCITY_ERROR]}")
        # print(f"{v[Register.CONTROL_TORQUE]} - {v[Register.TORQUE]} = {v[Register.TORQUE_ERROR]}")
        # print(f"{v[Register.POSITION_KP]} + {v[Register.POSITION_KI]} + {v[Register.POSITION_KD]} + {v[Register.POSITION_FEEDFORWARD]} = -1 * {v[Register.POSITION_COMMAND]}")

        print("----------")

            
        def verify(name, a, b, eps=1e-3):
            if math.isnan(a):
                a = 0
            diff = abs(a - b)
            if(diff > eps):
                print(f"{name}, Expected: {a} Actual: {b} Diff: {diff} - ERROR")
            else:
                print(f"{name}, Expected: {a} Actual: {b} Diff: {diff}")


        verify('Position', v[Register.CONTROL_POSITION] - v[Register.POSITION], -1 *v[Register.POSITION_ERROR])
        verify('Velocity', v[Register.CONTROL_VELOCITY] - v[Register.VELOCITY], -1*v[Register.VELOCITY_ERROR])
        verify('Torque', v[Register.CONTROL_TORQUE] - v[Register.TORQUE], -1*v[Register.TORQUE_ERROR])
        verify('PID', v[Register.POSITION_KP] + v[Register.POSITION_KI] + v[Register.POSITION_KD] + v[Register.POSITION_FEEDFORWARD],\
              -1 * v[Register.POSITION_COMMAND])


        await asyncio.sleep(0.25)

if __name__ == '__main__':
    asyncio.run(main())
