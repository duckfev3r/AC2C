import { Component, FunctionalComponent, h } from 'preact'
import * as style from './style.css'
import { WsService } from '../../services/ws.service'
import WalletController from 'lamden_wallet_controller'
import { config } from '../../../../shared/config'
import { GameDTO } from '../../../../shared/types'
import {
  checkForApproval,
  formatAccountAddress,
  returnFloat
} from '../../utils/utils'
import { TurnControls } from './TurnControls'

interface Props {}
interface State {
  wallet_info: string
  vk: string
  games_list: GameDTO[]
  player_games: GameDTO[]
  amount_input: number
  amount_approved?: number
  game_balance?: number
  wallet_balance?: number
}

const connectionRequest = {
  appName: 'AC2C', // Your DAPPS's name
  version: '0.0.1', // any version to start, increment later versions to update connection info
  logo: 'assets/apple-touch-icon.png', // or whatever the location of your logo
  contractName: config.master_contract, // Will never change
  networkType: 'testnet' // other option is 'mainnet'
}

class Home extends Component<Props, State> {
  ws = new WsService()
  connection = this.ws.connection
  lwc = new WalletController(connectionRequest)
  game_channels: string[] = []

  constructor(props) {
    super(props)

    this.state = {
      wallet_info: '',
      vk: '',
      games_list: [],
      player_games: [],
      amount_input: 10
    }

    this.connection.on('connect', () => {
      this.connection.on('global', msg => {})
      this.connection.on('games_list', games_list => {
        this.handleGamesListUpdate(games_list)
      })

      this.connection.on('joinedRoom', msg => {
        console.log('Joined Room', msg)
      })

      this.connection.on('balance_update', balance_dto => {
        console.log('BALANCE UPDATE', balance_dto)
        const { amount_approved, game_balance, wallet_balance } = balance_dto
        this.setState({ amount_approved, game_balance, wallet_balance })
      })

      this.connection.emit('joinRoom', 'global')
      this.connection.emit('joinRoom', 'balances')
    })

    const handleWalletInfo = wallet_info => {
      console.log('Wallet Info Update: ', wallet_info)
      console.log(wallet_info)
      const wallet_address = wallet_info.wallets[0]
      console.log(wallet_info.wallets)
      // if (!this.state.vk) {
      // }
      this.connection.emit('joinRoom', wallet_address)
      this.setState({
        wallet_info,
        vk: wallet_address
      })
    }
    const handleTxResults = txInfo =>
      console.log(`Transaction Submitted. `, txInfo)

    //Connect to event emitters
    this.lwc.events.on('newInfo', handleWalletInfo) // Wallet Info Events, including errors
    this.lwc.events.on('txStatus', handleTxResults) // Transaction Results
    console.log('Lamden Wallet Controller INIT', this.lwc)

    this.lwc.walletIsInstalled().then(installed => {
      if (installed) console.log('Lamden Wallet is Installed')
      else console.log('Lamden Wallet not Installed')
    })
  }

  handleGamesListUpdate = (games_list: GameDTO[]) => {
    games_list.sort((a, b) => b.players.length - a.players.length)

    const player_games = games_list.filter(table => {
      return table.players.indexOf(this.state.vk) > -1
    })

    // Add player to game room / will now receive state updates from the room.
    player_games.forEach(game => {
      if (this.game_channels.indexOf(game.game_id) < 0) {
        this.game_channels.push(game.game_id)
        // console.log(this.game_channels)
        console.log('attempting to join rooms...')
        console.log('game channels', this.game_channels)
        this.connection.on(game.game_id, game_update => {
          console.log(`game event : ${game_update.game_id} : `, game_update)

          const prev_state = this.state
          const player_games = prev_state.player_games
          const player_game_index = player_games.findIndex(
            game => game.game_id === game_update.game_id
          )
          player_games[player_game_index] = game_update

          const games_list = prev_state.games_list
          const game_index = games_list.findIndex(
            game => game.game_id === game_update.game_id
          )
          games_list[game_index] = game_update

          this.setState({ player_games, games_list })
        })
        this.connection.emit('joinRoom', game.game_id)
      }
    })

    // Remove player from any game rooms they're no longer a part of.
    const player_games_keys = player_games.map(game => game.game_id)
    this.game_channels.forEach(channel => {
      const game_channel_index = player_games_keys.indexOf(channel)
      if (game_channel_index < 0) {
        this.game_channels.splice(game_channel_index, 1)
        this.connection.off(channel)
        this.connection.emit('leaveRoom', channel)
      }
    })

    this.setState({ games_list, player_games }, () => {
      // console.log(this.state.games_list)
      // console.log(this.state.player_games)
    })
  }

  sendAddFundsTxn = (amount: number) => {
    const txInfo = {
      networkType: config.network, // other option is 'testnet'
      methodName: 'addFunds',
      kwargs: {
        amount: returnFloat(amount)
      },
      stampLimit: 150
    }

    const handleResults = txResults => console.log('Txn Results', txResults)

    this.lwc.sendTransaction(txInfo, handleResults) // callback is optional
  }

  sendCreateGame = () => {
    const txInfo = {
      networkType: config.network, // other option is 'testnet'
      methodName: 'createGame',
      kwargs: {
        number_of_seats: 2,
        ante: returnFloat(5)
      },
      stampLimit: 150
    }

    const handleResults = txResults => console.log('Txn Results', txResults)

    this.lwc.sendTransaction(txInfo, handleResults) // callback is optional
  }

  sendJoinTable = (game_id: string) => {
    const txInfo = {
      networkType: config.network,
      methodName: 'joinTable',
      kwargs: {
        game_id
      },
      stampLimit: 150
    }

    const handleResults = txResults =>
      console.log('Join Table Results', txResults)
    this.lwc.sendTransaction(txInfo, handleResults) // callback is optional
  }

  sendBet = (game_id: string, amount: number) => {
    const txInfo = {
      networkType: config.network,
      methodName: 'dealDecisionCard',
      kwargs: {
        game_id,
        amount
      },
      stampLimit: 150
    }
    const handleResults = txResults =>
      console.log('Send Bet Results', txResults)
    this.lwc.sendTransaction(txInfo, handleResults) // callback is optional
  }

  sendDealHand = (game_id: string) => {
    const txInfo = {
      networkType: config.network,
      methodName: 'dealHand',
      kwargs: {
        game_id
      },
      stampLimit: 150
    }
    const handleResults = txResults => {
      console.log('Deal Hand Results', txResults)
    }
    this.lwc.sendTransaction(txInfo, handleResults) // callback is optional
  }

  sendLeaveTable = (game_id: string) => {
    const txInfo = {
      networkType: config.network,
      methodName: 'leaveTable',
      kwargs: {
        game_id
      },
      stampLimit: 150
    }

    const handleResults = txResults =>
      console.log('Leave Table Results', txResults)
    this.lwc.sendTransaction(txInfo, handleResults) // callback is optional
  }

  handleJoinGame = (game_id: string) => {
    console.log('joining', game_id)
    this.connection.emit('joinRoom', game_id)
    this.sendJoinTable(game_id)
  }
  // Main keeps an updated list of games the user is a part of
  // Periodically checks that the user

  handleLeaveGame = (game_id: string) => {
    this.sendLeaveTable(game_id)
  }

  approveAndAdd = (amount, to) => {
    const transaction = {
      contractName: 'currency',
      methodName: 'approve',
      networkType: config.network,
      kwargs: {
        amount,
        to
      },
      stampLimit: 150
    }
    this.lwc.sendTransaction(transaction, res => {
      if (res.status === 'success') this.sendAddFundsTxn(amount)
    })
  }

  handleInput = e => {
    this.setState({ amount_input: e.target.value }, () => {
      console.log(this.state.amount_input)
    })
  }

  approveAndSend = async (add_amount: number, account: string) => {
    await checkForApproval(account).then((value: any) => {
      let parsed_value
      if (typeof value === 'object' && value?.__fixed__) {
        parsed_value = parseFloat(value.__fixed__)
      } else parsed_value = value
      if (parsed_value < add_amount) {
        let amount = add_amount - parsed_value
        console.log(amount)
        this.approveAndAdd(amount, config.master_contract)
      } else {
        this.sendAddFundsTxn(add_amount)
      }
    })
  }

  isAtTable = (vk: string, players: string[]) => {
    return players.indexOf(vk) > -1 ? true : false
  }

  handleBet = (game_id: string, amount: number) => {
    console.log(amount)
    this.sendBet(game_id, amount)
  }

  handleDealHand = (game_id: string) => {
    this.sendDealHand(game_id)
  }

  render() {
    const {
      games_list,
      amount_input,
      vk,
      amount_approved,
      game_balance,
      wallet_balance,
      player_games
    } = this.state
    return (
      <div>
        <div class={style.nav}>AC2C</div>
        <div class={style.main_container}>
          <div class={style.banking_panel}>
            account: {formatAccountAddress(vk)}
            <input
              value={amount_input}
              onInput={e => this.handleInput(e)}
              type="number"
            />
            <button
              onClick={() => {
                this.approveAndSend(amount_input, vk)
              }}
            >
              Add Chips
            </button>
            <div>Wallet Balance: {wallet_balance}</div>
            <div>Game Balance: {game_balance}</div>
            <div>Approved Amount: {amount_approved}</div>
          </div>
          <div class={style.table_container}>
            <div class={style.title_container}>
              <h2>Active Games</h2>
            </div>
            <div class={style.table_container_scroll}>
              <table>
                <tr>
                  <th>Table Name</th>
                  <th>Stakes</th>
                  <th>Players</th>
                  <th># of Seats</th>
                  <th></th>
                </tr>
                {games_list.map((game: GameDTO) => {
                  return (
                    <tr>
                      <td style={{ borderLeft: 'none' }}>{game.game_id}</td>
                      <td>
                        {game.ante} / {game.minimum_amount}
                      </td>
                      <td>{game.players.length}</td>
                      <td>{game.number_of_seats}</td>
                      <td style={{ textAlign: 'right' }}>
                        <div style={{ width: '100px' }}>
                          {!this.isAtTable(vk, game.players) ? (
                            <button
                              onClick={() => {
                                this.handleJoinGame(game.game_id)
                              }}
                            >
                              Join Game
                            </button>
                          ) : (
                            <button
                              onClick={() => {
                                this.handleLeaveGame(game.game_id)
                              }}
                            >
                              Leave Game
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </table>
            </div>
          </div>
        </div>
        <div>
          {player_games.map(game => (
            <div class={style.game_container}>
              <div class={style.game_main}>
                <div class={style.game_card_area}></div>
                <div class={style.game_player_area}>
                  {isActivePlayer(vk, game) && (
                    <TurnControls
                      game_id={game.game_id}
                      handleBet={this.handleBet}
                      handleDealHand={this.handleDealHand}
                    />
                  )}
                  {game.players.map(player => (
                    <div
                      class={style.game_player_container}
                      style={{
                        backgroundColor: isActivePlayer(player, game)
                          ? 'black'
                          : 'white'
                      }}
                    ></div>
                  ))}
                </div>
              </div>
              <div class={style.game_log}>Game Log Goes Here</div>
            </div>
          ))}
        </div>
      </div>
    )
  }
}

function isActivePlayer(player: string, game: GameDTO) {
  const { players, sitting_out, waiting } = game
  const not_in_game = [...sitting_out, ...waiting]
  const in_game: string[] = []
  players.forEach(p => {
    if (not_in_game.indexOf(p) < 0) in_game.push(p)
  })
  const player_index = in_game.indexOf(player)
  // console.log(players, sitting_out, waiting)
  // console.log(player)
  // console.log(in_game)
  // console.log(player_index)
  return game.round_index === player_index ? true : false
}

export default Home
