-- Plays a schedule of pad presses and captures, counted in vsyncs from power-on.
-- EMU_SCHED names the schedule file, EMU_OUT the output directory.
-- Each schedule line is "FRAME COMMAND [ARG]":
--   tap BUTTON        press for 6 frames (BUTTON as in PCSX.CONSTS.PAD.BUTTON)
--   hold BUTTON       press until released
--   release BUTTON
--   shot              write the frame to OUT/shots/sFRAME.raw
--   savestate NAME    write OUT/NAME.state
--   dump NAME         write main RAM to OUT/ram_NAME.bin
--   quit
local ffi = require('ffi')
local out = os.getenv('EMU_OUT')
local pad = PCSX.SIO0.slots[1].pads[1]
local B = PCSX.CONSTS.PAD.BUTTON

local byFrame = {}
local last = 0
for line in io.lines(os.getenv('EMU_SCHED')) do
  local f, cmd, arg = line:match('^(%d+)%s+(%S+)%s*(%S*)')
  if f then
    f = tonumber(f)
    byFrame[f] = byFrame[f] or {}
    table.insert(byFrame[f], { cmd, arg })
    if f > last then last = f end
  end
end

local releases = {}
local frame = 0

local function shot()
  local s = PCSX.GPU.takeScreenShot()
  local name = string.format('s%05d', frame)
  local f = io.open(out .. '/shots/' .. name .. '.raw', 'wb')
  f:write(tostring(s.data))
  f:close()
  print(string.format('SHOT %s %d %d', name, s.width, s.height))
end

local function run(cmd, arg)
  if cmd == 'tap' then
    pad.setOverride(B[arg])
    releases[frame + 6] = releases[frame + 6] or {}
    table.insert(releases[frame + 6], B[arg])
  elseif cmd == 'hold' then
    pad.setOverride(B[arg])
  elseif cmd == 'release' then
    pad.clearOverride(B[arg])
  elseif cmd == 'shot' then
    shot()
  elseif cmd == 'savestate' then
    local f = Support.File.open(out .. '/' .. arg .. '.state', 'TRUNCATE')
    f:writeMoveSlice(PCSX.createSaveState())
    f:close()
    print('SAVED ' .. arg)
  elseif cmd == 'dump' then
    local f = io.open(out .. '/ram_' .. arg .. '.bin', 'wb')
    f:write(ffi.string(PCSX.getMemPtr(), 0x200000))
    f:close()
    print('DUMPED ' .. arg)
  elseif cmd == 'quit' then
    PCSX.quit(0)
  end
end

driveListener = PCSX.Events.createEventListener('GPU::Vsync', function()
  frame = frame + 1
  for _, button in ipairs(releases[frame] or {}) do pad.clearOverride(button) end
  releases[frame] = nil
  for _, e in ipairs(byFrame[frame] or {}) do run(e[1], e[2]) end
  if frame > last then PCSX.quit(0) end
end)
