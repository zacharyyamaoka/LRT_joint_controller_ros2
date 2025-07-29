# moteus_controller <img src="https://github.com/KNR-PW/LRT_joint_controller_ros2/blob/main/joint_controller_test.gif" width="35" height="35" border="10"/>

## Introduction

This project provides a `ros2_control` `ChainableControllerInterface` used to simulate PID controller with position, velocity and feedforward effort inputs, like for example mjbots [moteus](https://github.com/mjbots/moteus) controller. It can simulate multiple controllers at the same time (for every actuated joint).

Controller is implementing following control law for every joint:

```math
\boldsymbol{\tau} = \boldsymbol{k}_{p_{scale}} \boldsymbol{k}_p(\boldsymbol{p}_{des} - \boldsymbol{p}) + \boldsymbol{k}_{d_{scale}} \boldsymbol{k}_d(\boldsymbol{v}_{des} - \boldsymbol{v}) + \boldsymbol{k}_i\int_{0}^{t} (\boldsymbol{p}_{des} - \boldsymbol{p}) \,dt  + \boldsymbol{\tau}_{ff}
```

where:

- $\boldsymbol{\tau}$: output joint effort
- $\boldsymbol{p}_{des}$: desired joint posistion
- $\boldsymbol{p}$: actual joint position
- $\boldsymbol{v_{des}}$: desired joint velocity
- $\boldsymbol{v}$: actual joint velocity
- $\boldsymbol{\tau}_{ff}$: feedforward joint effort
- $\boldsymbol{k}_p$, $\boldsymbol{k}_d$, $\boldsymbol{k}_i$: PID controller constant parameters
- $\boldsymbol{k}_ {p_{scale}}$: PID proportional dynamic parameter
- $\boldsymbol{k}_ {d_{scale}}$: PID derivative dynamic parameter

Reference (input) interfaces:

- $\boldsymbol{p}_{des}$: `position`
- $\boldsymbol{v_{des}}$: `velocity`
- $\boldsymbol{\tau}_{ff}$: `feedforward_torque`
- $\boldsymbol{k}_ {p_{scale}}$: `kp_scale`
- $\boldsymbol{k}_ {d_{scale}}$: `kd_scale`

User can choose what interfaces to use.

#### :warning: IMPORTANT: User don't have to use `velocity` interface for velocity part of PID to work, just add non-zero $\boldsymbol{k}_d$, desired velocity will always be zero, which creates virtual damping. It works similary for other interfaces.

### Software supports:

- :ballot_box_with_check: Working independently via subscriber using `moteus_controller/JointCommand` in `joint_controller_msgs` package
- :ballot_box_with_check: Working in chain mode with other controllers

### Differences to Moteus Controller

The moteus controller implements a two stage PID controller. One for the torque (included below), and one from torque to current. [View Docs](https://github.com/mjbots/moteus/blob/main/docs/reference.mdhttps:/)

```bash
acceleration = trajectory_follower(command_position, command_velocity)
control_velocity = command_velocity OR control_velocity + acceleration * dt OR 0.0
control_position = command_position OR control_position + control_velocity * dt
position_error = control_position - feedback_position
velocity_error = control_velocity - feedback_velocity
position_integrator = limit(position_integrator + ki * position_error * dt, ilimit)
torque = position_integrator +
         kp * kp_scale * position_error +
         kd * kd_scale * velocity_error +
         command_torque
```

Right now this package doesn't implement pure velocity control (something like `d pos nan -1 nan`) or `trajectory_follower` so the control signals are always calculated as:

```bash
control_velocity = command_velocity
control_position = command_position 
```

Another limitation is that it doesn't include the current controller. In simulation, a commanded torque is applied directly to the body. In reality, there is alot of error between the desired torque and actual torque being applied via current flowing through motor windings.

In the current state this package should provide a good first order approximation to the Moteus Controller. [Some inital work ](https://github.com/KNR-PW/LRT_one_power_unit_identification/tree/main/optimizationhttps:/)has been done on system identification between this virtual controller and the real controller, but requires further investigation.

### sim2real:

A major use of this package is for doing sim2real transfer for robots running with moteus controllers.

For accurate sim2real:

- Set the PID parameters of the joints to be identical to the ones used in moteus system
- Set Interial properties of urdf links accurately
- Set friction properties of urdf links accurately

## ROS 2 version

- Humble (supports `ros2_control` for Rolling)

## Dependencies (all for humble)

- [ros2_control](https://github.com/ros-controls/ros2_control)
- [ros2_controllers](https://github.com/ros-controls/ros2_controllers)
- [generate_parameter_library](https://github.com/PickNikRobotics/generate_parameter_library)
  - This allows you to dynamically update Parameters at runtime which can be helpful for tunning the PID!
- sensor_msgs

## Installation

1. Clone repo to your workspace:

```bash
git clone https://github.com/KNR-PW/LRT_joint_controller_ros2.git
```

2. Install dependencies in workspace:

```bash
rosdep install --ignore-src --from-paths . -y -r
```

3. Build:

```bash
colcon build --packages-select joint_controller_msgs moteus_controller
```

### Controller parameters (example):

**Position control:**
```yaml
...
moteus_controller:
      type: moteus_controller/MoteusController
...
moteus_controller:
  ros__parameters:
    joint_names:
      - body_1_joint

    command_interface: "position"  # Forwards position commands directly

    joint_params:
      body_1_joint: 
        position_max: 3.14
        position_min: -3.14
        position_offset: 0.0
        velocity_max: 10.0
        effort_max: 10.0
  
    reference_interfaces: 
      - "position"

    frequency: 500.0

    pid_gains:
      body_1_joint:
        p: 1.0
        d: 0.5
        i: 0.0
        ilimit: 1.0
...
```

#### `joint_names` - names of joints

#### `joint_params` (map for every joint name):

- `position_offset` - Position offset, will be added to commanded position before sending to controller [`radians`]
- `position_max/min` - Max/min position [`radians`]
- `velocity_max` - Maximal velocity [`radians`]
- `effort_max` - Maximal torque [`Nm`]

#### `reference_interfaces` - reference (input) interfaces for user or other controller

#### `command_interface` - Command interface type. Can be "effort" (default) or "position". When set to "effort", the controller calculates torque using PID control. When set to "position", the controller forwards the commanded position directly to the hardware.

#### `state_interface` - :warning: ALWAYS POSITION AND VELOCITY, NOTHING ELSE (it is deafult value so user don't have to write it)

#### `frequency` - frequency for PID controller (only usefull in integral term), that have to be same as real frequency [Hz]

#### `pid_gains` (map for every joint name):

- `p` - proportional PID term
- `d` - derivative PID term
- `i` - integral PID term
- `ilimit` - integration limit [`Nm`]

## Troubleshooting/New functionality

#### Add new `Issue`. I will try my best to answer. You can also contribute to project via pull requests.

## Contributing

1. Change code.
2. Run all launchfile tests.
3. Check performance, compliance and other functionality via e.g. [plotjugller](https://plotjuggler.io/) for `ros2`.
4. Add clear description what changes you've made in pull request.
