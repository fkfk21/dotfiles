local status, ibl = pcall(require, "ibl")
if not status then
	return
end

local highlight = {
    "CursorColumn",
    "Whitespace",
}
require("ibl").setup()

