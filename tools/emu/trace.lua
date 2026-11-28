-- Logs calls to the functions listed in EMU_TRACE (lines "ADDR SIGNATURE NAME", from sigs.py).
-- Overlays share addresses, so a hit only counts when the code bytes at ADDR match SIGNATURE.
-- Needs the interpreter (-interpreter -debugger); the dynarec doesn't stop on breakpoints.
-- Prints the first EMU_TRACE_LOG hits of each function (default 8) as HIT lines, and one
-- CALLS line per function that ran when the emulator quits.
local ffi = require('ffi')
local mem = ffi.cast('uint8_t*', PCSX.getMemPtr())
local maxLog = tonumber(os.getenv('EMU_TRACE_LOG') or '8')

local function rd8(a) return mem[bit.band(a, 0x1fffff)] end

local function matches(a, sig)
  for i = 0, #sig / 2 - 1 do
    if rd8(a + i) ~= tonumber(sig:sub(i * 2 + 1, i * 2 + 2), 16) then return false end
  end
  return true
end

local function bytesAt(v, n)
  if v < 0x80000000 or v >= 0x80200000 then return '-' end
  local t = {}
  for i = 0, n - 1 do t[#t + 1] = string.format('%02x', rd8(v + i)) end
  return table.concat(t)
end

local frame = 0
traceFrames = PCSX.Events.createEventListener('GPU::Vsync', function() frame = frame + 1 end)

local stats = {}
traceBreakpoints = {}
for line in io.lines(os.getenv('EMU_TRACE')) do
  local addr, sig, name = line:match('^(%x+)%s+(%x+)%s+(%S+)')
  if addr then
    local a = tonumber(addr, 16)
    local st = { name = name, count = 0, callers = {}, ncallers = 0 }
    stats[#stats + 1] = st
    -- The callback returns true to keep the breakpoint; false would remove it after one hit.
    traceBreakpoints[#traceBreakpoints + 1] = PCSX.addBreakpoint(a, 'Exec', 4, name, function()
      if not matches(a, sig) then return true end
      local r = PCSX.getRegisters().GPR.n
      st.count = st.count + 1
      if st.count == 1 then st.first = frame end
      st.last = frame
      if not st.callers[r.ra] and st.ncallers < 4 then
        st.callers[r.ra] = true
        st.ncallers = st.ncallers + 1
      end
      if st.count <= maxLog then
        print(string.format('HIT %s frame=%d ra=%08x a0=%08x a1=%08x a2=%08x a3=%08x *a0=%s',
          name, frame, r.ra, r.a0, r.a1, r.a2, r.a3, bytesAt(r.a0, 32)))
      end
      return true
    end)
  end
end

traceQuit = PCSX.Events.createEventListener('Quitting', function()
  for _, st in ipairs(stats) do
    if st.count > 0 then
      local c = {}
      for ra in pairs(st.callers) do c[#c + 1] = string.format('%08x', ra) end
      table.sort(c)
      print(string.format('CALLS %s count=%d first=%d last=%d callers=%s',
        st.name, st.count, st.first, st.last, table.concat(c, ',')))
    end
  end
end)
print('TRACE armed ' .. #traceBreakpoints)
