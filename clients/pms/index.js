const { app, BrowserWindow } = require('electron')

 // Create the browser window.
const createWindow = () => {

  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    backgroundColor: '#ffffff',
    transparent: false,
    title: 'Orchestrading',
    titleBarOverlay: {
        color: '#2f3241',
        symbolColor: '#74b1be',
        height: 60}
  })

  //win.loadFile('index.html')
  win.loadURL('http://localhost:5000');
}

app.whenReady().then(() => {
  createWindow()
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })

})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit()
})
