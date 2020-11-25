# ACEY DUCEY

## Game Rules

* Game goes in rounds.
* Play proceeds clockwise.
* Each time a player takes a turn a new round is started.
* At the start of each round, every player at the table pays an ante.
* Two cards are then dealt face-up.
* The player whose turn it is, then gets to bet if the value of the next card drawn will fall between the two which are currently in play.
* A player can decide not to bet, in which case play skips them.
* Players can bet up to the value of the pot.
* If a player guesses wrong, their bet is added to the pot and play proceeds.
* If the card drawn has the same value as either of the two cards drawn, they must pay 2x their bet, then play proceeds.

## Skipping Players

* If a player is taking too long, the next player at the table may wish to skip them in play.
* A variable will be set for the game which defines what the timeout should be before a player can be skipped
* Once this amount of time has passed, an inactive player can be skipped.

## Table Rules

* When a player joins a table, there is a minimum buyin, these funds are transfered to the contract and returned when the user leaves the table.

## Scaling

* It may be necessary at a later date to introduce a server to manage state, which can be requested from a masternode. eg. https://mainnet.lamden.io/api/states/history/con_token_swap