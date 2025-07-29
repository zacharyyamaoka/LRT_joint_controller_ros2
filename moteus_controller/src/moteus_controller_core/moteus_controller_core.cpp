#include "moteus_controller/moteus_controller_core/moteus_controller_core.hpp"
#include <iostream>   // for std::cout
#include <iomanip>    // for std::setprecision

using namespace moteus_controller_core;

MoteusControllerCore::MoteusControllerCore(JointParameters _joint_params,
 pid_controller::PidParameters _pid_params, double _frequency): 
    joint_params_(_joint_params), pid_controller_(_pid_params, _frequency){}

double MoteusControllerCore::calculateEffort(const JointCommands& _joint_command,const JointStates& _joint_state)
{
    double desired_position = std::clamp(_joint_command.desired_position_ + joint_params_.position_offset_,
         joint_params_.position_min_, joint_params_.position_max_);
    double desired_velocity = std::clamp(_joint_command.desired_velocity_,
     -joint_params_.velocity_max_, joint_params_.velocity_max_);

    double position_error = desired_position - _joint_state.position_;
    double velocity_error = desired_velocity - _joint_state.velocity_;
    double effort =  pid_controller_.calculateEffort(position_error, velocity_error,
     _joint_command.feedforward_effort_, _joint_command.kp_scale_, _joint_command.kd_scale_);


    // std::cout << std::fixed << std::setprecision(4);
    // std::cout << "[calculateEffort] desired_position: " << desired_position << std::endl;
    // std::cout << "[calculateEffort] desired_velocity: " << desired_velocity << std::endl;
    // std::cout << "[calculateEffort] position_error: " << position_error << std::endl;
    // std::cout << "[calculateEffort] velocity_error: " << velocity_error << std::endl;
    // std::cout << "[calculateEffort] effort (before clamp): " << effort << std::endl;

     effort = std::clamp(effort, -joint_params_.effort_max_, joint_params_.effort_max_);

    _total_effort = effort;

    // std::cout << "[calculateEffort] effort (after clamp): " << effort << std::endl;

    return effort;
}

ControllerState MoteusControllerCore::queryState() const
{
    ControllerState state;
    state.P = pid_controller_.P;
    state.I = pid_controller_.I;
    state.D = pid_controller_.D;
    state.FF = pid_controller_.FF;
    state.total_effort = _total_effort;
    return state;
}