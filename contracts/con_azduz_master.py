import con_ac2c_methods_01
import currency

S = Hash(default_value='')
Balances = Hash(default_value=0)
Owner = Variable()

@construct
def seed():
    Owner.set(ctx.caller)

@export
def setName(name: str):
    key = ctx.caller
    name_taken = S['name_to_key', name]
    previous_name = S['key_to_name', key]

    # assert bool(re.match("^[A-Za-z0-9_-\s]*$", name)), 'Only Letters, numbers, dashes and underscores allowed'
    assert len(name) > 1 and len(name) < 15, 'Chosen name length must be more than 1 and less then 15 characters long.'
    assert name_taken is None, 'This name has been taken.'

    S['key_to_name', key] = name
    S['name_to_key', name] = key 

    if previous_name is not None:
        S['name_to_key', previous_name] = None


# Banking

@export 
def addFunds(amount: float):
    assert amount > 0, 'Amount must be greater than 0.'
    currency.transfer_from(amount=amount, to = ctx.this, main_account = ctx.caller)
    
    if Balances[ctx.caller] is None:
        Balances[ctx.caller] = amount
    else:
        Balances[ctx.caller] += amount

    return {'new_balance': Balances[ctx.caller]}

@export 
def transferFunds(amount: float, to: str):
    assert amount > 0, 'Amount must be greater than 0.'
    assert Balances[ctx.caller] >= amount, "You don't have enough to make this transfer."
    
    balance_to = Balances[to]
    balance_sender = Balances[ctx.caller]

    if Balances[to] is None or Balances[ctx.caller] == 0:
        Balances[to] = amount
    else:
        Balances[to] += amount
        
    Balances[ctx.caller] -= amount

    response = {'to:': { 'new_balance': Balances[to], 'old_balance': balance_to},'sender': {'new_balance': Balances[ctx.caller], 'old_balance': balance_sender}}

    return response

@export 
def withdrawFunds(amount: float):
    balance = Balances[ctx.caller]
    assert balance >= amount, 'You cannot withdraw more than ' + balance
    currency.transfer(amount = amount, to=ctx.caller)
    Balances[ctx.caller] = balance - amount

# Game Methods

@export
def createGame(number_of_seats: int, ante: float):
    random.seed()
    # For Development
    game_id = str(random.randint(0,99999999999999999))

    contract_owner = Owner.get()
    # Checks
    assert contract_owner == ctx.caller, "You are " + ctx.caller + ", should be " + contract_owner
    assert S['games', game_id] is not None, "Game " + game_id + " already exists."
    assert ante > 0, "Ante must be more than 0."
    assert number_of_seats > 1 and number_of_seats <= 8, "The number of seats must be more than 1 and less than 9"

    # To Do - Checks on Values needed here, e.g no negative numbers allowed, check values exist.

    # Setup Game State

    S['games',game_id,'game_state'] = "idle"
    S['games',game_id,'number_of_seats'] = number_of_seats
    S['games',game_id,'host'] = ctx.caller
    S['games',game_id,'players'] = []
    S['games',game_id,'sitting_out'] = []
    S['games',game_id,'waiting'] = []
    S['games',game_id,'leaving'] = []
    S['games',game_id,'ante'] = ante
    S['games',game_id,'minimum_amount'] = number_of_seats * ante * 2
    S['games',game_id,'pot_size'] = 0
    S['games',game_id,'round_index'] = 0
    S['games',game_id,'orbit_count'] = 0

    response = {
        'game_id': game_id,
    }

    return response

@export
def joinTable(game_id: str):
    player = ctx.caller
    number_of_seats = S['games',game_id,'number_of_seats'] 
    minimum_amount = S['games',game_id,'minimum_amount']
    players = S['games', game_id, 'players']
    sitting_out = S['games',game_id,'sitting_out']
    waiting = S['games',game_id,'waiting']
    game_state = S['games',game_id,'game_state']


    active_players = getActivePlayers(players = players, waiting = waiting, sitting_out = sitting_out)

    player_balance = Balances[player]
    # Checks

    assert player not in players, "You're already in this game."
    assert player_balance is not None and not 0, 'You must add funds before you can sit at a table'
    assert int(minimum_amount) <= int(player_balance), 'The minimum buyin for this game is ' + str(minimum_amount)
    assert number_of_seats is not None, "The game you're trying to join with id " + game_id + " does not exist."
    assert number_of_seats >= len(players), 'Game is full !'

    # Add Player to Table

    players.append(player)
    S['games', game_id, 'players'] = players

    if game_state != 'idle':
        waiting.append(player)
        S['games',game_id,'waiting'] = waiting
    else: 
        decideStartRound(game_id = game_id)

    return game_id

@export
def decideStartRound(game_id: str):
    game_state = S['games',game_id,'game_state']
    players = S['games', game_id, 'players']
    sitting_out = S['games',game_id,'sitting_out']
    orbit_count = S['games',game_id,'orbit_count']
    round_index = S['games',game_id,'round_index']
    waiting = S['games',game_id,'waiting']

    active_players = getActivePlayers(players = players, sitting_out = sitting_out, waiting = waiting)
    if len(active_players) > 1 and round_index == 0:
        startRound(game_id = game_id)
    else:
        S['games',game_id,'game_state'] = 'idle'

@export
def startRound(game_id: str):
    ante = S['games', game_id, 'ante']
    players = S['games', game_id, 'players']
    pot_size = S['games', game_id, 'pot_size']
    sitting_out = S['games', game_id, 'sitting_out']
    waiting = S['games',game_id,'waiting']
    S['games',game_id,'game_state'] = 'playing'

    antes_total = ante * S['games', game_id, 'number_of_seats']

    to_sit_out = [p for p in players if Balances[p] < antes_total]
    sitting_out.append(to_sit_out)
    S['games',game_id,'sitting_out'] = sitting_out

    active_players = getActivePlayers(players = players, waiting = waiting, sitting_out = sitting_out)

    to_take = ante * len(active_players)

    for p in active_players:
        player_balance = Balances[p]
        if player_balance >= to_take:
            player_balance -= to_take
            Balances[p] = player_balance
        else:
            sitting_out.append(p)
            S['games', game_id, 'sitting_out'] = sitting_out
    
    # dealHand(game_id = game_id)

@export 
def getActivePlayers(players: list, sitting_out: list, waiting: list):
    out_of_play = sitting_out + waiting
    active_players = [p for p in players if p not in out_of_play]
    return active_players

@export
def dealHand(game_id: str):
    random.seed()
    players = S['games', game_id, 'players']
    sitting_out = S['games',game_id,'sitting_out']
    waiting = S['games',game_id,'waiting']
    ante = S['games', game_id, 'ante']
    pot_size = S['games', game_id, 'pot_size']
    round_index = S['games',game_id,'round_index']

    active_players = getActivePlayers(players = players, sitting_out = sitting_out, waiting = waiting)
    new_pot_value = incrementPotByAntes(pot_size = pot_size, ante = ante, active_players = active_players)

    assert ctx.caller in active_players, "You must be a participant in this game to deal the hand."

    active_player = active_players[round_index]

    card_methods = con_ac2c_methods_01
    S['games', game_id, 'pot_size'] = new_pot_value

    # Deal the cards.
    rail_cards = card_methods.dealRailCards()
    S['games',game_id,'dealt_cards','card_1'] = rail_cards['card_1']
    S['games',game_id,'dealt_cards','card_2'] = rail_cards['card_2']

    return {'rail_cards': rail_cards}

@export
def incrementPotByAntes(pot_size: float, ante: float, active_players: list ):
    increment_by = len(active_players) * ante
    pot_size += increment_by
    return pot_size

# To Be Called by player whose turn it is

@export
def dealDecisionCard(game_id: str, amount: float):
    random.seed()
    player = ctx.caller
    players = S['games', game_id, 'players']
    sitting_out = S['games',game_id,'sitting_out']
    waiting = S['games',game_id,'waiting']
    round_index = S['games',game_id,'round_index']
    pot_size = S['games',game_id,'pot_size']
    card_1 = S['games',game_id,'dealt_cards','card_1']
    card_2 = S['games',game_id,'dealt_cards','card_2']
    
    active_players = getActivePlayers(players = players, sitting_out = sitting_out, waiting = waiting)
    active_player = active_players[round_index]
    player_balance = Balances[player]
    minimum_balance_allowed = amount * 2

    assert player == active_player, 'Only the active player can deal the decision card. Needs to be : ' + active_player + ' , was called by ' + player
    assert amount <= pot_size, 'You cannot bet more then the pot'
    assert player_balance >= minimum_balance_allowed, 'Your balance is too small to make this bet. You need a minimum of '+ minimum_balance_allowed

    # Deal decision card.

    card_methods = con_ac2c_methods_01

    dealt_cards = {
        'card_1': card_1,
        'card_2': card_2
    }
    dealt_cards['decision_card'] = card_methods.getUniqueCard(existing_cards = dealt_cards)

    S['games',game_id,'dealt_cards'] = dealt_cards
    result = card_methods.decideResult(dealt_cards)
    
    final_balances = calcDecisionCardBalance(
        result = result, 
        player_balance = player_balance, 
        pot_size = pot_size, 
        amount = amount
        )

    Balances[player] = final_balances['player_balance']
    S['games',game_id,'pot_size'] = final_balances['pot_size']
    
    endHand(
        game_id = game_id,
        active_players = active_players, 
        round_index = round_index,
        players = players
        )

@export
def endHand(game_id: str, active_players: list, round_index: int, players: list):
    S['games',game_id,'dealt_cards']
    leaving = S['games',game_id,'leaving']

    if round_index + 1 == len(active_players):
        S['games',game_id,'round_index'] = 0
        S['games',game_id,'waiting'] = []
        orbit_count = S['games',game_id,'orbit_count']
        S['games',game_id,'orbit_count'] = orbit_count + 1
        # decideStartRound(game_id = game_id)

        if len(leaving) > 0:
            players = S['games',game_id,'players']
            S['games',game_id,'players'] = removeLeaving(game_id = game_id, leaving = leaving)
            S['games',game_id,'leaving'] = []

    else:
        S['games',game_id,'round_index'] = round_index + 1

@export
def removeLeaving(players: list, leaving: list):
    for p in leaving:
        players.remove(p)
    
    return players

@export
def calcDecisionCardBalance(result: str, player_balance: float, pot_size: float, amount: float):
    if result == 'win':
        player_balance += pot_size
        pot_size -= amount
    elif result == 'lose':
        player_balance -= amount
        pot_size += amount
    else:
        double_bet = amount * 2
        player_balance -= double_bet
        pot_size += double_bet
    return {
        'pot_size': pot_size,
        'player_balance': player_balance,
    }

@export
def leaveTable(game_id: str):
    player = ctx.caller
    leaving = S['games',game_id,'leaving']
    players = S['games',game_id,'players']
    game_state = S['games', game_id, 'game_state']

    assert S['games',game_id,'number_of_seats'] is not None, "Game doesn't exist."
    assert player in players, "You're not at this table. You need to sit down before you can leave."
    assert player not in leaving, "You're already waiting to leave this table."

    if game_state is not 'idle' :
        leaving.append(player)
        S['games',game_id,'leaving'] = leaving
    else :
        players.remove(player)
        S['games', game_id, 'players'] = players

@export 
def cancelLeave(game_id: str, player: str):
    leaving = S['games',game_id,'leaving']

    assert player in leaving, "You're not waiting to leave this table."

    leaving.remove(player)
    S['games',game_id,'leaving'] = leaving

