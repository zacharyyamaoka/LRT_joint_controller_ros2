# Introspect moteus_controller

# Inspired by
# https://github.com/ros-controls/control_msgs/blob/master/control_msgs/msg/JointTrajectoryControllerState.msg

# Field names are selected to match telemetry data from
# python3 -m moteus_gui.tview --devices=1
# and commands: d pos nan 0 nan p0 d0 f0.01 a0.5 v1

std_msgs/Header header

# DoF name, e.g., joint or Cartesian axis name
string[] name

# Control signal / setpoint
float64[] control_position
float64[] control_velocity
float64[] feedforward # feedforward torque in Nm
float64[] kp # dynamic parameter
float64[] kd # dynamic parameter
float64[] max_torque # max torque in Nm

# Current value of the process (ie: latest sensor measurement on the controlled value).
float64[] position
float64[] velocity
float64[] torque # in Nm

# PID values
float64[] p # = k_p * k_p_static * (error)
float64[] i # sum of integral term
float64[] d # = k_d * k_d_static * (error_rate)
float64[] command # Output of PID + feedforward, in Nm 

# Note in the real moteus the feedforward term take 1 control cycle to incoperate