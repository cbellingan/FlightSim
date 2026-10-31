--
-- JUST FLIGHT CESSNA 152 - MOZA AY210 INTEGRATION SCRIPT
-- Combined Master ALT/BAT, Avionics->Pitot, Rotary Magnetos & Authentic O-235-L2C Mag Drop
-- MOZA Gear Switch to Parking Brake Set/Disengage
--

-- DATAREFS
simDR_battery_on       = find_dataref("sim/cockpit2/electrical/battery_on[0]")
simDR_generator_on     = find_dataref("sim/cockpit2/electrical/generator_on[0]")
simDR_pitot_heat       = find_dataref("sim/cockpit2/ice/ice_pitot_heat_on_pilot")
simDR_ignition_pos     = find_dataref("sim/cockpit2/engine/actuators/ignition_key[0]")
simDR_ignition_on      = find_dataref("sim/cockpit2/engine/actuators/ignition_on[0]")
simDR_engine_rpm       = find_dataref("sim/cockpit2/engine/indicators/engine_speed_rpm[0]")
simDR_override_thro    = find_dataref("sim/operation/override/override_throttles")
simDR_engn_thro        = find_dataref("sim/flightmodel/engine/ENGN_thro[0]")
simDR_engn_thro_use    = find_dataref("sim/flightmodel/engine/ENGN_thro_use[0]")
simDR_park_brake       = find_dataref("sim/cockpit2/controls/parking_brake_ratio")

thrandaDR_starter_key  = find_dataref("thranda/starter_key1")
thrandaDR_hidepilot    = find_dataref("thranda/views/hidepilot")
thrandaDR_hidecopilot  = find_dataref("thranda/views/hidecopilot")

-- 1. COMBINED MASTER ALT / BAT (MOZA BATT SWITCH)
function C152_bat_on_before(phase, duration)
	if phase == 0 or phase == 1 then
		if simDR_battery_on ~= nil then simDR_battery_on = 1 end
		if simDR_generator_on ~= nil then simDR_generator_on = 1 end
	end
	return 0
end

function C152_bat_off_before(phase, duration)
	if phase == 0 or phase == 1 then
		if simDR_battery_on ~= nil then simDR_battery_on = 0 end
		if simDR_generator_on ~= nil then simDR_generator_on = 0 end
	end
	return 0
end

simCMD_bat1_on_wrap  = wrap_command("sim/electrical/battery_1_on",   C152_bat_on_before,  nil)
simCMD_bat_all_on    = wrap_command("sim/electrical/battery_all_on", C152_bat_on_before,  nil)
simCMD_bat1_off_wrap = wrap_command("sim/electrical/battery_1_off",  C152_bat_off_before, nil)
simCMD_bat2_off_wrap = wrap_command("sim/electrical/battery_2_off",  C152_bat_off_before, nil)
simCMD_bat_all_off   = wrap_command("sim/electrical/battery_all_off", C152_bat_off_before, nil)

-- 2. AVIONICS / PITOT LINKING
function C152_pitot_on_before(phase, duration)
	if phase == 0 or phase == 1 then
		if simDR_pitot_heat ~= nil then simDR_pitot_heat = 1 end
	end
	return 0
end

function C152_pitot_off_before(phase, duration)
	if phase == 0 or phase == 1 then
		if simDR_pitot_heat ~= nil then simDR_pitot_heat = 0 end
	end
	return 0
end

simCMD_av_on_wrap    = wrap_command("sim/systems/avionics_on",     C152_pitot_on_before,  nil)
simCMD_av_off_wrap   = wrap_command("sim/systems/avionics_off",    C152_pitot_off_before, nil)
simCMD_pitot_on_wrap = wrap_command("sim/ice/pitot_heat0_on",      C152_pitot_on_before,  nil)
simCMD_pitot_off_wrap= wrap_command("sim/ice/pitot_heat0_off",     C152_pitot_off_before, nil)

-- 3. DIRECT ROTARY MAGNETO SWITCH HANDLERS
function C152_mag_off_before(phase, duration)
	if phase == 0 or phase == 1 then
		if simDR_ignition_pos ~= nil then simDR_ignition_pos = 0 end
		if simDR_ignition_on  ~= nil then simDR_ignition_on  = 0 end
		if thrandaDR_starter_key ~= nil then thrandaDR_starter_key = 0 end
	end
	return 0
end

function C152_mag_right_before(phase, duration)
	if phase == 0 or phase == 1 then
		if simDR_ignition_pos ~= nil then simDR_ignition_pos = 1 end
		if simDR_ignition_on  ~= nil then simDR_ignition_on  = 1 end
		if thrandaDR_starter_key ~= nil then thrandaDR_starter_key = 1 end
	end
	return 0
end

function C152_mag_left_before(phase, duration)
	if phase == 0 or phase == 1 then
		if simDR_ignition_pos ~= nil then simDR_ignition_pos = 2 end
		if simDR_ignition_on  ~= nil then simDR_ignition_on  = 2 end
		if thrandaDR_starter_key ~= nil then thrandaDR_starter_key = 2 end
	end
	return 0
end

function C152_mag_both_before(phase, duration)
	if phase == 0 or phase == 1 then
		if simDR_ignition_pos ~= nil then simDR_ignition_pos = 3 end
		if simDR_ignition_on  ~= nil then simDR_ignition_on  = 3 end
		if thrandaDR_starter_key ~= nil then thrandaDR_starter_key = 3 end
	end
	return 0
end

function C152_starter_before(phase, duration)
	if phase == 0 or phase == 1 then
		if simDR_ignition_pos ~= nil then simDR_ignition_pos = 4 end
		if simDR_ignition_on  ~= nil then simDR_ignition_on  = 3 end
		if thrandaDR_starter_key ~= nil then thrandaDR_starter_key = 4 end
	elseif phase == 2 then
		if simDR_ignition_pos ~= nil then simDR_ignition_pos = 3 end
		if simDR_ignition_on  ~= nil then simDR_ignition_on  = 3 end
		if thrandaDR_starter_key ~= nil then thrandaDR_starter_key = 3 end
	end
	return 1
end

simCMD_mag_off_wrap   = wrap_command("sim/magnetos/magnetos_off",     C152_mag_off_before,   nil)
simCMD_mag_off1_wrap  = wrap_command("sim/magnetos/magnetos_off_1",   C152_mag_off_before,   nil)
simCMD_mag_right_wrap = wrap_command("sim/magnetos/magnetos_right_1", C152_mag_right_before, nil)
simCMD_mag_left_wrap  = wrap_command("sim/magnetos/magnetos_left_1",  C152_mag_left_before,  nil)
simCMD_mag_both_wrap  = wrap_command("sim/magnetos/magnetos_both",    C152_mag_both_before,  nil)
simCMD_mag_both1_wrap = wrap_command("sim/magnetos/magnetos_both_1",  C152_mag_both_before,  nil)
simCMD_starter_wrap   = wrap_command("sim/starters/engage_starter_1", C152_starter_before,   nil)

-- 4. PARKING BRAKE COMMAND HANDLERS (MOZA GEAR SWITCH INTEGRATION)
function C152_park_brake_set_before(phase, duration)
	if phase == 0 or phase == 1 then
		if simDR_park_brake ~= nil then simDR_park_brake = 1.0 end
	end
	return 0
end

function C152_park_brake_rel_before(phase, duration)
	if phase == 0 or phase == 1 then
		if simDR_park_brake ~= nil then simDR_park_brake = 0.0 end
	end
	return 0
end

simCMD_pb_set_wrap = wrap_command("sim/flight_controls/park_brake_set",     C152_pb_set_before, nil)
simCMD_pb_rel_wrap = wrap_command("sim/flight_controls/park_brake_release", C152_pb_rel_before, nil)

-- 5. RUNTIME PHYSICS & PILOT SUPPRESSION
function before_physics()
	-- Suppress pilot renders if datarefs are exposed by SASL
	if thrandaDR_hidepilot ~= nil and thrandaDR_hidepilot ~= 1 then
		thrandaDR_hidepilot = 1
	end
	if thrandaDR_hidecopilot ~= nil and thrandaDR_hidecopilot ~= 1 then
		thrandaDR_hidecopilot = 1
	end

	-- Authentic C152 Lycoming O-235-L2C run-up magneto drop (~65-75 RPM drop at 1700 RPM)
	if simDR_ignition_pos ~= nil and simDR_engine_rpm ~= nil and simDR_override_thro ~= nil and simDR_engn_thro ~= nil and simDR_engn_thro_use ~= nil then
		if (simDR_ignition_pos == 1 or simDR_ignition_pos == 2) and simDR_engine_rpm > 450 then
			local rpm_scale = math.min(1.0, math.max(0.0, (simDR_engine_rpm - 550.0) / 1150.0))
			local delta = (simDR_ignition_pos == 1 and 0.028 or 0.031) * rpm_scale
			simDR_override_thro = 1
			simDR_engn_thro_use = math.max(0.0, simDR_engn_thro - delta)
		else
			if simDR_override_thro == 1 then
				simDR_override_thro = 0
				simDR_engn_thro_use = simDR_engn_thro
			end
		end
	end
end

function aircraft_unload()
	if simDR_override_thro ~= nil and simDR_override_thro == 1 then
		simDR_override_thro = 0
	end
end
