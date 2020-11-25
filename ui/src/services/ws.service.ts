import socket from 'socket.io-client'

export class WsService {
    connection: SocketIOClient.Socket = socket('http://localhost:3000')
    constructor() {
        this.setupEvents()
    }

    setupEvents = () => {
        this.connection.on('connect', () => {
            console.log('Websocket Connected.')
        })
        this.connection.on('event', data => {
            console.log('Websocket Event', data)
        })
        this.connection.on('disconnect', () => {
            console.log('Websocket Client Disconnected.')
        })
    }
}