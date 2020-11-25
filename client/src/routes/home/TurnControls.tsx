import { Component, FunctionalComponent, h } from 'preact'
import { useState } from 'preact/hooks'

export function TurnControls(props: any) {
  const [value, updateValue] = useState(0)
  const { handleBet, handleDealHand, game_id } = props

  const handleUpdateValue = e => {
    console.log(e)
  }

  return (
    <div>
      <button
        onClick={() => {
          handleBet(game_id, value)
        }}
      >
        Bet
      </button>
      <button onClick={() => handleDealHand(game_id)}>Deal Hand</button>
      <button onClick={() => handleBet(game_id, 0)}>Pass</button>
      <input value={value} onChange={handleUpdateValue} type="number" />
    </div>
  )
}
