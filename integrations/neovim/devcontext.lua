-- DevContext integration for Neovim
-- Add to your init.lua: require('devcontext')

local M = {}

-- Create floating window for output
local function show_float(output, title)
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
    border = 'rounded',
    title = title or 'DevContext',
    title_pos = 'center'
  })

  -- Close on q or Esc
  vim.keymap.set('n', 'q', ':close<CR>', { buffer = buf, silent = true })
  vim.keymap.set('n', '<Esc>', ':close<CR>', { buffer = buf, silent = true })
end

function M.start()
  vim.fn.system('devctx start')
  vim.notify('DevContext session started', vim.log.levels.INFO)
end

function M.stop()
  local output = vim.fn.system('devctx end')
  show_float(output, ' Session Summary ')
end

function M.note(text)
  vim.fn.system('devctx note "' .. text .. '"')
  vim.notify('Note added: ' .. text, vim.log.levels.INFO)
end

function M.resume()
  local output = vim.fn.system('devctx resume')
  show_float(output, ' Resume Context ')
end

function M.status()
  local output = vim.fn.system('devctx status')
  print(output)
end

function M.summary()
  local output = vim.fn.system('devctx summary')
  show_float(output, ' Session Summary ')
end

function M.setup(opts)
  opts = opts or {}

  -- Create commands
  vim.api.nvim_create_user_command('DevCtxStart', M.start, {})
  vim.api.nvim_create_user_command('DevCtxEnd', M.stop, {})
  vim.api.nvim_create_user_command('DevCtxNote', function(o) M.note(o.args) end, { nargs = '+' })
  vim.api.nvim_create_user_command('DevCtxResume', M.resume, {})
  vim.api.nvim_create_user_command('DevCtxStatus', M.status, {})
  vim.api.nvim_create_user_command('DevCtxSummary', M.summary, {})

  -- Optional keymaps
  if opts.keymaps ~= false then
    local prefix = opts.prefix or '<leader>d'
    vim.keymap.set('n', prefix .. 's', M.start, { desc = 'DevContext Start' })
    vim.keymap.set('n', prefix .. 'e', M.stop, { desc = 'DevContext End' })
    vim.keymap.set('n', prefix .. 'n', ':DevCtxNote ', { desc = 'DevContext Note' })
    vim.keymap.set('n', prefix .. 'r', M.resume, { desc = 'DevContext Resume' })
    vim.keymap.set('n', prefix .. 't', M.status, { desc = 'DevContext Status' })
  end

  -- Auto session management
  if opts.auto_session then
    vim.api.nvim_create_autocmd('VimEnter', {
      callback = function()
        local status = vim.fn.system('devctx status 2>&1')
        if not status:match('not initialized') then
          M.start()
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
  end
end

return M
