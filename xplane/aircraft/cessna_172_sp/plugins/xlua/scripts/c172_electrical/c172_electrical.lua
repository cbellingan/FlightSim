
----------------------------------------------------------------------------------------------------------
-- THIS SCRIPT ANIMATE SLOWLY THE CUSTOM AMP GAUGE;
-- PLUS, IT AUTOMATICALLY SWITCH ON/OFF THE CROSS TIE IN THE CESSNA G1000 DEPENDING ON BUS VOLTS (RELAY);
-- AND THEN, IT HANDLE THE ALT/BAT MASTER SWITCHES LOGIC (mechanically interlocked in the real Cessna)
-- PLUS MOZA AY210 COMBINED MASTER ALT+BAT AND AVIONICS BUS 1+2 SWITCH LINKING.
----------------------------------------------------------------------------------------------------------

-------------------------------------------------------------------------------------
-- PS1: IN THE ANALOGIC C172 THE TWO AVIONIC BUSES ARE SIMULATED USING THE CROSS-TIE
-- (AVIONIC-BUS1 IS THE ACTUAL AVIONIC SWITCH, AVIONIC-BUS2 IS THE CROSS-TIE SWITCH)
-- SO THE BUS1 AND BUS2 STUFF OF THE POH ALL GOES TO BUS1 IN PLANEMAKER
-- WHILE ONLY THE AVIONIC BUS2 STUFF GOES TO BUS2 IN PLANEMAKER
-------------------------------------------------------------------------------------

-------------------------------------------------------------------------------------
-- PS2: IN THE G1000 C172 THE 2 AVIONIC BUSES ARE NOT SIMULATED
-- AND THE TWO AVIONIC SWITCHES ALL POINT TO THE SAME AVIONICS COMMAND ON-OFF
-------------------------------------------------------------------------------------




----------------------------------- LOCATE AND/OR CREATE DATAREFS -----------------------------------

battery_amps = find_dataref("sim/cockpit2/electrical/battery_amps[0]")
main_bus_volts = find_dataref("sim/cockpit2/electrical/bus_volts[0]")
max_bat_volt_standard = find_dataref("sim/aircraft/limits/max_bat_volt_standard") -- the nominal battery volts from acf planemaker
cross_tie = find_dataref("sim/cockpit2/electrical/cross_tie")
generator_on = find_dataref("sim/cockpit2/electrical/generator_on[0]")
battery_on = find_dataref("sim/cockpit2/electrical/battery_on[0]")
avionics_on = find_dataref("sim/cockpit2/switches/avionics_power_on")
num_batteries = find_dataref("sim/aircraft/electrical/num_batteries") -- we use this to know whether we are on the G1000 or analogue cessna

battery_amps_c172 = create_dataref("laminar/c172/electrical/battery_amps","number") -- the instrument needle

simCMD_gen1_on  = find_command("sim/electrical/generator_1_on")
simCMD_gen1_off = find_command("sim/electrical/generator_1_off")



---------------------------------------- FUNCTIONS ---------------------------------------

-- ANIMATION OF THE AMPS NEEDLE
function update_amps_needles()
	battery_amps_c172 = battery_amps_c172 + ((battery_amps_c172NEW - battery_amps_c172) * (10 * SIM_PERIOD))
end

-- MOZA AY210 COMBINED MASTER ALT + BAT HANDLERS
function bat1_on_before(phase, duration) end
function bat1_on_after(phase, duration)
	if phase == 0 then
		battery_on = 1
		generator_on = 1
		if simCMD_gen1_on ~= nil then command_once(simCMD_gen1_on) end
		batteryPREV = 1
		generatorPREV = 1
	end
end

function bat1_off_before(phase, duration) end
function bat1_off_after(phase, duration)
	if phase == 0 then
		battery_on = 0
		generator_on = 0
		if simCMD_gen1_off ~= nil then command_once(simCMD_gen1_off) end
		batteryPREV = 0
		generatorPREV = 0
	end
end

function bat2_off_before(phase, duration) end
function bat2_off_after(phase, duration)
	if phase == 0 and num_batteries == 1 then
		battery_on = 0
		generator_on = 0
		batteryPREV = 0
		generatorPREV = 0
	end
end

-- MOZA AY210 COMBINED AVIONICS BUS 1 + BUS 2 HANDLERS
function avio_on_before(phase, duration) end
function avio_on_after(phase, duration)
	if phase == 0 then
		avionics_on = 1
		if num_batteries == 1 then
			cross_tie = 1
		end
		avionicsPREV = 1
	end
end

function avio_off_before(phase, duration) end
function avio_off_after(phase, duration)
	if phase == 0 then
		avionics_on = 0
		if num_batteries == 1 then
			cross_tie = 0
		end
		avionicsPREV = 0
	end
end

function avio_tog_before(phase, duration) end
function avio_tog_after(phase, duration)
	if phase == 0 and num_batteries == 1 then
		cross_tie = avionics_on
		avionicsPREV = avionics_on
	end
end

-- Keep global references to all command objects so Lua GC never collects them
cmd_master_both_on  = create_command("laminar/c172/electrical/master_alt_bat_on", "Master ALT + BAT Both ON (MOZA BATT)", bat1_on_after)
cmd_master_both_off = create_command("laminar/c172/electrical/master_alt_bat_off", "Master ALT + BAT Both OFF (MOZA BATT)", bat1_off_after)
cmd_avionics_both_on  = create_command("laminar/c172/electrical/avionics_bus_1_2_on", "Avionics Bus 1 + Bus 2 Both ON (MOZA PITOT)", avio_on_after)
cmd_avionics_both_off = create_command("laminar/c172/electrical/avionics_bus_1_2_off", "Avionics Bus 1 + Bus 2 Both OFF (MOZA PITOT)", avio_off_after)

simCMD_bat1_on  = wrap_command("sim/electrical/battery_1_on", bat1_on_before, bat1_on_after)
simCMD_bat1_off = wrap_command("sim/electrical/battery_1_off", bat1_off_before, bat1_off_after)
simCMD_bat2_off = wrap_command("sim/electrical/battery_2_off", bat2_off_before, bat2_off_after)
simCMD_avio_on  = wrap_command("sim/systems/avionics_on", avio_on_before, avio_on_after)
simCMD_avio_off = wrap_command("sim/systems/avionics_off", avio_off_before, avio_off_after)
simCMD_avio_tog = wrap_command("sim/systems/avionics_toggle", avio_tog_before, avio_tog_after)




----------------------------------- RUNTIME CODE -----------------------------------


-- REGULAR RUNTIME
function after_physics()

	-- UPDATE AMPS NEEDLE
	battery_amps_c172NEW = battery_amps
	update_amps_needles()


	-- CROSS-TIE RELAY ON THE G1000 CESSNA
	if num_batteries == 2 then
		if main_bus_volts > max_bat_volt_standard then cross_tie = 1 else cross_tie = 0 end
	end


	-- ALT/BAT MASTER SWITCHES LOGIC (SYNC BOTH ON & OFF)
	if batteryPREV ~= battery_on then
		if battery_on == 0 then
			generator_on = 0
			if simCMD_gen1_off ~= nil then command_once(simCMD_gen1_off) end
		end
		if battery_on == 1 then
			generator_on = 1
			if simCMD_gen1_on ~= nil then command_once(simCMD_gen1_on) end
		end
	end
	if generatorPREV ~= generator_on then
		if generator_on == 1 then battery_on = 1 end
	end
	batteryPREV = battery_on
	generatorPREV = generator_on


	-- AVIONICS BUS 1 & BUS 2 SYNC LOGIC (ANALOG / SEAPLANE C172)
	if avionicsPREV ~= avionics_on then
		if num_batteries == 1 then
			cross_tie = avionics_on
		end
	end
	avionicsPREV = avionics_on

end
