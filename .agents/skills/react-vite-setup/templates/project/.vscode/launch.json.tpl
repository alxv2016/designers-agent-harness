{
  // Chrome with the debugger attached, on the ports the web app spec names. Start the server first — `npm run dev`
  // or `npm run storybook` — so the one already running is the one debugged.
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Debug app in Chrome",
      "type": "chrome",
      "request": "launch",
      "url": "http://localhost:{{dev_port}}",
      "webRoot": "${workspaceFolder}"
    },
    {
      "name": "Debug Storybook in Chrome",
      "type": "chrome",
      "request": "launch",
      "url": "http://localhost:{{storybook_port}}",
      "webRoot": "${workspaceFolder}"
    }
  ]
}
