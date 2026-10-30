--
-- THIS SCRIPT CREATES THE CUSTOM COMMANDS TO HANDLE THE OFF/R/L/BOTH/START IGNITION KEY
-- AND PROVIDES REALISTIC SINGLE-MAGNETO RPM DROP FOR THE CESSNA 172 SP
--

-- LOCATE DATAREFS AND COMMANDS

simDR_ignition_pos     = find_dataref("sim/cockpit2/engine/actuators/ignition_key[0]")
simDR_ignition_on      = find_dataref("sim/cockpit2/engine/actuators/ignition_on[0]")
simDR_engine_rpm       = find_dataref("sim/cockpit2/engine/indicators/engine_speed_rpm[0]")
simDR_override_thro    = find_dataref("sim/operation/override/override_throttles")
simDR_engn_thro        = find_dataref("sim/flightmodel/engine/ENGN_thro[0]")
simDR_engn_thro_use    = find_dataref("sim/flightmodel/engine/ENGN_thro_use[0]")

simCMD_ignition_down_1 = find_command("sim/magnetos/magnetos_down_1")
simCMD_ignition_up_1   = find_command("sim/magnetos/magnetos_up_1")
simCMD_engage_starter  = find_command("sim/starters/engage_starter_1")

-- 3D COCKPIT CLICK MANIPULATOR HANDLERS

function C172_ignition_down_CMDhandler(phase, duration)
	if phase == 0 then
		if simDR_ignition_pos ~= 4 then
			simCMD_ignition_down_1:once()
		end
	end
end

function C172_ignition_up_CMDhandler(phase, duration)
	if phase == 0 then
		if simDR_ignition_pos == 3 or simDR_ignition_pos == 4 then
			simCMD_engage_starter:start()
		elseif simDR_ignition_pos < 3 then
			simCMD_ignition_up_1:once()
		end
	elseif phase == 2 then
		if simDR_ignition_pos == 4 then
			simCMD_engage_starter:stop()
		end
	end
end

-- DIRECT ROTARY SWITCH COMMAND WRAPPERS
-- Guarantees 100% reliable hardware rotary switch positioning (OFF / R / L / BOTH / START)
-- without relying on X-Plane's multi-engine rocker toggle logic.

function C172_mag_off_before_CMDhandler(phase, duration)
	if phase == 0 or phase == 1 then
		simDR_ignition_pos = 0
		simDR_ignition_on  = 0
	end
	return 0
end

function C172_mag_right_before_CMDhandler(phase, duration)
	if phase == 0 or phase == 1 then
		simDR_ignition_pos = 1
		simDR_ignition_on  = 1
	end
	return 0
end

function C172_mag_left_before_CMDhandler(phase, duration)
	if phase == 0 or phase == 1 then
		simDR_ignition_pos = 2
		simDR_ignition_on  = 2
	end
	return 0
end

function C172_mag_both_before_CMDhandler(phase, duration)
	if phase == 0 or phase == 1 then
		simDR_ignition_pos = 3
		simDR_ignition_on  = 3
	end
	return 0
end

function C172_starter_before_CMDhandler(phase, duration)
	if phase == 0 or phase == 1 then
		simDR_ignition_pos = 4
		simDR_ignition_on  = 3
	elseif phase == 2 then
		simDR_ignition_pos = 3
		simDR_ignition_on  = 3
	end
	return 1
end

-- REGISTER WRAPPED HARDWARE COMMANDS
simCMD_mag_off_wrap   = wrap_command("sim/magnetos/magnetos_off",     C172_mag_off_before_CMDhandler,   nil)
simCMD_mag_off1_wrap  = wrap_command("sim/magnetos/magnetos_off_1",   C172_mag_off_before_CMDhandler,   nil)
simCMD_mag_right_wrap = wrap_command("sim/magnetos/magnetos_right_1", C172_mag_right_before_CMDhandler, nil)
simCMD_mag_left_wrap  = wrap_command("sim/magnetos/magnetos_left_1",  C172_mag_left_before_CMDhandler,  nil)
simCMD_mag_both_wrap  = wrap_command("sim/magnetos/magnetos_both",    C172_mag_both_before_CMDhandler,  nil)
simCMD_mag_both1_wrap = wrap_command("sim/magnetos/magnetos_both_1",  C172_mag_both_before_CMDhandler,  nil)
simCMD_starter_wrap   = wrap_command("sim/starters/engage_starter_1", C172_starter_before_CMDhandler,  nil)

-- CREATE VIRTUAL COCKPIT COMMANDS
C172CMD_ignition_down = create_command("laminar/c172/ignition_down", "Ignition Sel Down", C172_ignition_down_CMDhandler)
C172CMD_ignition_up   = create_command("laminar/c172/ignition_up",   "Ignition Sel Up",   C172_ignition_up_CMDhandler)

-- RUNTIME MAGNETO CHECK RPM DROP SIMULATION
-- Authentic Lycoming IO-360-L2A magneto check drop (~85-95 RPM drop at 1800 RPM)
function before_physics()
	if (simDR_ignition_pos == 1 or simDR_ignition_pos == 2) and simDR_engine_rpm > 450 then
		local rpm_scale = math.min(1.0, math.max(0.0, (simDR_engine_rpm - 600.0) / 1200.0))
		local delta = (simDR_ignition_pos == 1 and 0.032 or 0.035) * rpm_scale
		simDR_override_thro = 1
		simDR_engn_thro_use = math.max(0.0, simDR_engn_thro - delta)
	else
		if simDR_override_thro == 1 then
			simDR_override_thro = 0
			simDR_engn_thro_use = simDR_engn_thro
		end
	end
end

function aircraft_unload()
	if simDR_override_thro == 1 then
		simDR_override_thro = 0
	end
end
