@export
def dealRailCards():
    values = []
    cards = dict()
    card_1 = getUniqueRailCard([])
    card_2 = getUniqueRailCard([card_1])
    cards['card_1'] = card_1
    cards['card_2'] = card_2
    return cards

@export 
def getUniqueRailCard(existing_card: list): 
    if len(existing_card) == 0:
        index = getRandomCard()
        return {'index': index, 'value': getCardValue(index)}
    else:
        new_card_index = getRandomCard()
        new_card_value = getCardValue(new_card_index)
        if new_card_index == existing_card[0]['index']:
            return getUniqueRailCard(existing_card)
        else: 
            return {'index': new_card_index,'value': new_card_value}

@export 
def getUniqueCard(existing_cards: dict):
    new_card_index = getRandomCard()
    exists = False
    for key in existing_cards:
        if existing_cards[key]['index'] == new_card_index:
            return getUniqueCard(existing_cards)
    else:
        return {'index': new_card_index, 'value': getCardValue(new_card_index)}

@export
def decideResult(cards: dict):
    rail_cards = [cards['card_1']['value'], cards['card_2']['value']]
    rail_cards.sort()
    decision_card = cards['decision_card']['value']
    if decision_card < rail_cards[0] or decision_card > rail_cards[1]:
        return 'lose'
    if decision_card == rail_cards[0] or decision_card == rail_cards[1]:
        return 'rail'
    else:
        return 'win'

@export
def getCardValue(index:int):
    divided = int(index / 13)
    to_subtract = divided * 13
    value = index - to_subtract
    return value

@export
def getRandomCard():
    card_index = random.randint(0,51)
    return card_index
