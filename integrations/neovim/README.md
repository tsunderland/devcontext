# DevContext Integration for Neovim

## Lua Plugin Setup

Add DevContext commands to your Neovim config.

### Basic Setup (init.lua)

```lua
-- DevContext commands
vim.api.nvim_create_user_command('DevCtxStart', function()
  vim.fn.system('devctx start')
  print('DevContext session started')
end, {})

vim.api.nvim_create_user_command('DevCtxEnd', function()
  local output = vim.fn.system('devctx end')
  -- Show in floating window
  local buf = vim.api.nvim_create_buf(false, true)
  vim.api.nvim_buf_set_lines(buf, 0, -1, false, vim.split(output, '\n'))
  local width = math.floor(vim.o.columns * 0.8)
  local height = math.floor(vim.o.lines * 0.6)
  vim.api.nvim_open_win(buf, true, {
    relative = 'editor',
    width = width,
    height = height,
    row = math.floor((vim.o.lines - height) / 2),
    col = math.floor((vim.o.columns - width) / 2),
    style = 'minimal',
    border = 'rounded'
  })
end, {})

vim.api.nvim_create_user_command('DevCtxNote', function(opts)
  vim.fn.system('devctx note "' .. opts.args .. '"')
  print('Note added: ' .. opts.args)
end, { nargs = '+' })

vim.api.nvim_create_user_command('DevCtxResume', function()
  local output = vim.fn.system('devctx resume')
  local buf = vim.api.nvim_create_buf(false, true)
  vim.api.nvim_buf_set_lines(buf, 0, -1, false, vim.split(output, '\n'))
  local width = math.floor(vim.o.columns * 0.8)
  local height = math.floor(vim.o.lines * 0.6)
  vim.api.nvim_open_win(buf, true, {
    relative = 'editor',
    width = width,
    height = height,
    row = math.floor((vim.o.lines - height) / 2),
    col = math.floor((vim.o.columns - width) / 2),
    style = 'minimal',
    border = 'rounded'
  })
end, {})

vim.api.nvim_create_user_command('DevCtxStatus', function()
  print(vim.fn.system('devctx status'))
end, {})

vim.api.nvim_create_user_command('DevCtxSummary', function()
  local output = vim.fn.system('devctx summary')
  local buf = vim.api.nvim_create_buf(false, true)
  vim.api.nvim_buf_set_lines(buf, 0, -1, false, vim.split(output, '\n'))
  local width = math.floor(vim.o.columns * 0.8)
  local height = math.floor(vim.o.lines * 0.6)
  vim.api.nvim_open_win(buf, true, {
    relative = 'editor',
    width = width,
    height = height,
    row = math.floor((vim.o.lines - height) / 2),
    col = math.floor((vim.o.columns - width) / 2),
    style = 'minimal',
    border = 'rounded'
  })
end, {})

-- Keymaps (optional)
vim.keymap.set('n', '<leader>ds', ':DevCtxStart<CR>', { desc = 'DevContext Start' })
vim.keymap.set('n', '<leader>de', ':DevCtxEnd<CR>', { desc = 'DevContext End' })
vim.keymap.set('n', '<leader>dn', ':DevCtxNote ', { desc = 'DevContext Note' })
vim.keymap.set('n', '<leader>dr', ':DevCtxResume<CR>', { desc = 'DevContext Resume' })
vim.keymap.set('n', '<leader>dt', ':DevCtxStatus<CR>', { desc = 'DevContext Status' })
```

### Commands

| Command | Description |
|---------|-------------|
| `:DevCtxStart` | Start session |
| `:DevCtxEnd` | End session with summary |
| `:DevCtxNote <text>` | Add a note |
| `:DevCtxResume` | Show resume context |
| `:DevCtxStatus` | Show session status |
| `:DevCtxSummary` | Mid-session summary |

### Keymaps

With the optional keymaps above:

| Key | Action |
|-----|--------|
| `<leader>ds` | Start session |
| `<leader>de` | End session |
| `<leader>dn` | Add note (enter text after) |
| `<leader>dr` | Resume context |
| `<leader>dt` | Status |

## Avante.nvim / AI Plugin Integration

If using AI plugins like avante.nvim:

```lua
-- Get DevContext summary for AI context
local function get_devcontext()
  return vim.fn.system('devctx resume')
end

-- Add to your AI plugin's context
-- (Implementation depends on the specific plugin)
```

## Auto-Session Integration

Auto-start sessions when opening Neovim in a tracked project:

```lua
vim.api.nvim_create_autocmd('VimEnter', {
  callback = function()
    -- Check if project is tracked
    local status = vim.fn.system('devctx status 2>&1')
    if not status:match('not initialized') then
      vim.fn.system('devctx start')
    end
  end
})

vim.api.nvim_create_autocmd('VimLeavePre', {
  callback = function()
    local status = vim.fn.system('devctx status 2>&1')
    if status:match('Active') then
      vim.fn.system('devctx end')
    end
  end
})
```
