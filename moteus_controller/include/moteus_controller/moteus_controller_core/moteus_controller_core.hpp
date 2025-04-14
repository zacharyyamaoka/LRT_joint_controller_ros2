#ifndef _MOTEUS_CONTROLLER_CORE_HPP_
#define _MOTEUS_CONTROLLER_CORE_HPP_

#include "moteus_controller/pid_controller/pid_controller.hpp"
#include <algorithm>

namespace moteus_controller_core
{
    struct JointParameters
    {
        double position_max_ = 0;       /* [radians] or [m]*/
        double position_min_ = 0;       /* [radians] or [m]*/
        double position_offset_ = 0;    /* [radians]  or [m]*/
        double velocity_max_ = 0;       /* [radians/s] or [m/s]*/
        double effort_max_ = 0;         /* [Nm] or [N]*/
    };

    struct JointStates
    {
        double position_ = 0;            /* [radians] or [m]*/
        double velocity_ = 0;            /* [radians/s] or [m/s]*/
        double effort_ = 0;              /* [Nm] or [N]*/
    };

    struct JointCommands
    {
        double desired_position_ = 0;   /* [radians] or [m]*/
        double desired_velocity_ = 0;   /* [radians/s] or [m/s]*/
        double kp_scale_ = 1;           
        double kd_scale_ = 1;
        double feedforward_effort_ = 0; /* [Nm] or [N]*/
    };


    class MoteusControllerCore
    {
        private:

        /* Joint parameters */
        JointParameters joint_params_;

        /* Internal PID controller parameters */
        pid_controller::PidController pid_controller_;

        public:

        MoteusControllerCore(JointParameters _joint_params,
         pid_controller::PidParameters _pid_params, double _frequency);
        MoteusControllerCore(const MoteusControllerCore& other) = default;
        MoteusControllerCore(MoteusControllerCore&& other) = default;

        /* Effort calculation */
        double calculateEffort(const JointCommands& _joint_command,const JointStates& _joint_state);
        
    };
};

#endif

