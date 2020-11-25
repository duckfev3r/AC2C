import unittest

from contracting.db.driver import ContractDriver, Driver
from contracting.client import ContractingClient

class MyTestCase(unittest.TestCase):

    def setUp(self):
        self.c = ContractingClient()
        self.c.flush()

        with open('con_azduz_card_methods.py') as f:
            code = f.read()
            self.c.submit(code, name='con_azduz_card_methods')

        with open('currency.s.py') as f:
            code = f.read()
            self.c.submit(code, name='currency', constructor_args={'vk':'sys'})

        with open('con_azduz_master.py') as f:
            code = f.read()
            self.c.submit(code, name='con_azduz_master')

        self.game_contract = self.c.get_contract('con_azduz_master')
        self.currency_contract = self.c.get_contract('currency')

    def tearDown(self):
        self.c.flush()

    def test_00a_ownership(self):
        owner = self.game_contract.quick_read('Owner')
        self.assertEqual(owner, 'sys')

    def test_01a_transferFunds(self):
        # Approve Add funds to 'sys'
        self.currency_contract.approve(amount = 10, to = 'con_azduz_master')
        # Add Funds to 'sys'
        self.game_contract.addFunds(amount = 10)
        test_res = self.game_contract.transferFunds(signer = "sys", amount = 10, to = 'benji')
        self.assertEqual(self.game_contract.quick_read('Balances', 'benji'), 10)
        self.assertEqual(self.game_contract.quick_read('Balances', 'sys'), 0)
        with self.assertRaises(AssertionError):
            self.game_contract.transferFunds(signer = "sys", amount = 100, to = 'benji')

    def test_02a_createGame(self):
        ante = 5
        number_of_seats = 4
        game = self.game_contract.createGame(number_of_seats = number_of_seats, ante = ante)
        game_id = game['game_id']
        print(game)
        # game_state should be 'idle'
        game_state_key = 'games' + ':' + game['game_id']+':'+'game_state'
        self.assertEqual(self.game_contract.quick_read('S', game_state_key),'idle')

        game_ante_key = 'games' + ':' + game['game_id'] + ':ante'
        self.assertEqual(self.game_contract.quick_read('S', game_ante_key), ante)

        game_seats_key = 'games' + ':' + game['game_id'] + ':number_of_seats'
        self.assertEqual(self.game_contract.quick_read('S', game_seats_key), number_of_seats)

    def test_02b_createGame(self):
        with self.assertRaises(AssertionError):
            join_table_res = game = self.game_contract.createGame(number_of_seats = 10, ante = 4)

        with self.assertRaises(AssertionError):
            join_table_res = game = self.game_contract.createGame(number_of_seats = -10, ante = 4)

        with self.assertRaises(AssertionError):
            join_table_res = game = self.game_contract.createGame(number_of_seats = 4, ante = -4)

    def test_03a_joinTable(self):
        # Fails, user balance is less then number_of_seats * ante
        game = self.game_contract.createGame(number_of_seats = 4, ante = 5)
        game_id = game['game_id']

        self.currency_contract.approve(amount = 10, to = 'con_azduz_master')
        self.game_contract.addFunds(amount = 10)

        test_res = self.game_contract.transferFunds(signer = "sys", amount = 10, to = 'benji')
        with self.assertRaises(AssertionError):
            join_table_res = self.game_contract.joinTable(signer = 'benji', game_id = game_id)

        self.assertEqual(self.game_contract.quick_read('Balances', 'benji'), 10)
        self.assertEqual(self.game_contract.quick_read('Balances', 'sys'), 0)

    def test_03b_joinTable(self):
        game = self.game_contract.createGame(number_of_seats = 4, ante = 5)
        game_id = game['game_id']

        self.currency_contract.approve(amount = 80, to = 'con_azduz_master')
        self.game_contract.addFunds(amount = 80)

        test_res = self.game_contract.transferFunds(signer = "sys", amount = 80, to = 'benji')
        join_table_res = self.game_contract.joinTable(signer = 'benji', game_id = game_id)

        table_players_key = 'games' + ':' + game['game_id'] + ':players'
        self.assertEqual(len(self.game_contract.quick_read('S', table_players_key)), 1)

    def test_03c_joinTable(self):
        game = self.game_contract.createGame(number_of_seats = 4, ante = 5)
        game_id = game['game_id']

        self.currency_contract.approve(amount = 80, to = 'con_azduz_master')
        self.game_contract.addFunds(amount = 80)

        test_res = self.game_contract.transferFunds(signer = "sys", amount = 80, to = 'benji')
        join_table_res = self.game_contract.joinTable(signer = 'benji', game_id = game_id)

        table_players_key = 'games' + ':' + game['game_id'] + ':players'
        self.assertEqual(len(self.game_contract.quick_read('S', table_players_key)), 1)
        # self.assertEqual(self.game_contract.quick_read('Balances', 'sys'), 0)

    def test_03d_joinTable(self):
        game = self.game_contract.createGame(number_of_seats = 4, ante = 5)
        game_id = game['game_id']

        self.currency_contract.approve(amount = 160, to = 'con_azduz_master')
        self.game_contract.addFunds(amount = 160)

        self.game_contract.transferFunds(signer = "sys", amount = 160, to = 'benji')

        self.game_contract.joinTable(signer = 'benji', game_id = game_id)

        with self.assertRaises(AssertionError):
            join_table_res = self.game_contract.joinTable(signer = 'benji', game_id = game_id)

    # Waiting Flow Checks

    def test_03e_joinTable(self):
        game = self.game_contract.createGame(number_of_seats = 5, ante = 5)
        game_id = game['game_id']

        self.currency_contract.approve(amount = 10000, to = 'con_azduz_master')
        self.game_contract.addFunds(amount = 10000)

        test_res = self.game_contract.transferFunds(signer = "sys", amount = 80, to = 'benji')
        test_res = self.game_contract.transferFunds(signer = "sys", amount = 80, to = 'mick')
        test_res = self.game_contract.transferFunds(signer = "sys", amount = 80, to = 'julia')        
        test_res = self.game_contract.transferFunds(signer = "sys", amount = 80, to = 'fred')
        test_res = self.game_contract.transferFunds(signer = "sys", amount = 80, to = 'mona')

        # Players benji + mick sit down and a round begins

        self.game_contract.joinTable(signer = 'benji', game_id = game_id)
        self.game_contract.joinTable(signer = 'mick', game_id = game_id)

        table_players_key = 'games' + ':' + game['game_id'] + ':game_state'
        self.assertEqual(self.game_contract.quick_read('S', table_players_key), 'playing')

        waiting_key = 'games' + ':' + game['game_id'] + ':waiting'
        waiting = self.game_contract.quick_read('S', waiting_key)

        players_key = 'games' + ':' + game['game_id'] + ':players'
        players = self.game_contract.quick_read('S', players_key)

        self.assertEqual(len(waiting), 0)
        self.assertEqual(len(players), 2)

        # Julia joins and as the round has begun, joins the waitlist

        self.game_contract.joinTable(signer = 'julia', game_id = game_id)

        players_key = 'games' + ':' + game['game_id'] + ':players'
        players = self.game_contract.quick_read('S', players_key)

        waiting_key = 'games' + ':' + game['game_id'] + ':waiting'
        waiting = self.game_contract.quick_read('S', waiting_key)

        self.assertEqual(len(waiting), 1)
        self.assertEqual(len(players), 3)

        ## Benji + Mick both take their turns, round ends and Julia is removed from the waitlist

        self.game_contract.dealHand(signer = 'benji', game_id = game_id)
        self.game_contract.dealDecisionCard(game_id = game_id, amount = 4, signer='benji')
        self.game_contract.dealHand(signer = 'benji', game_id = game_id)
        self.game_contract.dealDecisionCard(game_id = game_id, amount = 4, signer='mick')


        players = self.game_contract.quick_read('S', players_key)
        waiting = self.game_contract.quick_read('S', waiting_key)

        self.assertEqual(len(waiting), 0)
        self.assertEqual(len(players), 3)

        # Fred and Mona sit down, and again must wait for the round to complete before he can play.

        self.game_contract.joinTable(signer = 'fred', game_id = game_id)
        self.game_contract.joinTable(signer = 'mona', game_id = game_id)

        players = self.game_contract.quick_read('S', players_key)
        waiting = self.game_contract.quick_read('S', waiting_key)

        self.assertEqual(len(waiting), 2)
        self.assertEqual(len(players), 5)

        self.game_contract.dealDecisionCard(signer = 'benji', game_id = game_id, amount = 4)
        self.game_contract.dealDecisionCard(signer='mick', game_id = game_id, amount = 4)

        players = self.game_contract.quick_read('S', players_key)
        waiting = self.game_contract.quick_read('S', waiting_key)

        self.assertEqual(len(waiting), 2)
        self.assertEqual(len(players), 5)

        self.game_contract.dealDecisionCard(signer = 'julia', game_id = game_id, amount = 4)

        players = self.game_contract.quick_read('S', players_key)
        waiting = self.game_contract.quick_read('S', waiting_key)

        print(players)
        print(waiting)

        self.assertEqual(len(waiting), 0)
        self.assertEqual(len(players), 5)

        self.game_contract.dealDecisionCard(signer = 'benji', game_id = game_id, amount = 4)
        self.game_contract.dealDecisionCard(signer = 'mick', game_id = game_id, amount = 4)
        self.game_contract.dealDecisionCard(signer = 'julia', game_id = game_id, amount = 4)
        self.game_contract.dealDecisionCard(signer = 'fred', game_id = game_id, amount = 4)
        self.game_contract.dealDecisionCard(signer = 'mona', game_id = game_id, amount = 4)



    # Checking Balance Deductions work correctly.

    def test_03f_joinTable(self):
        game = self.game_contract.createGame(number_of_seats = 5, ante = 5)
        game_id = game['game_id']

        self.currency_contract.approve(amount = 10000, to = 'con_azduz_master')
        self.game_contract.addFunds(amount = 10000)

        players_key = 'games' + ':' + game['game_id'] + ':players'
        players = self.game_contract.quick_read('S', players_key)
        waiting_key = 'games' + ':' + game['game_id'] + ':waiting'
        waiting = self.game_contract.quick_read('S', waiting_key)
        sitting_out_key = 'games' + ':' + game['game_id'] + ':sitting_out'
        sitting_out = self.game_contract.quick_read('S', sitting_out_key)
    
        buy_in = 80

        self.game_contract.transferFunds(signer = "sys", amount = buy_in, to = 'benji')
        self.game_contract.transferFunds(signer = "sys", amount = buy_in, to = 'mick')
        self.game_contract.transferFunds(signer = "sys", amount = buy_in, to = 'julia')        
        self.game_contract.transferFunds(signer = "sys", amount = buy_in, to = 'fred')
        self.game_contract.transferFunds(signer = "sys", amount = buy_in, to = 'mona')

        # Players benji + mick sit down and a round begins

        self.game_contract.joinTable(signer = 'benji', game_id = game_id)
        self.game_contract.joinTable(signer = 'mick', game_id = game_id)

        self.game_contract.dealHand(signer = 'benji', game_id = game_id)
        self.game_contract.dealDecisionCard(game_id = game_id, amount = 4, signer='benji')
        self.game_contract.dealHand(signer = 'benji', game_id = game_id)
        self.game_contract.dealDecisionCard(game_id = game_id, amount = 4, signer='mick')

        self.game_contract.decideStartRound(game_id = game_id)
        self.game_contract.dealHand(signer = 'benji', game_id = game_id)
        self.game_contract.dealDecisionCard(game_id = game_id, amount = 4, signer='benji')
        self.game_contract.dealHand(signer = 'benji', game_id = game_id)
        self.game_contract.dealDecisionCard(game_id = game_id, amount = 4, signer='mick')
        
        active_players = self.game_contract.getActivePlayers(players = players, sitting_out = sitting_out, waiting = waiting)
        total_player_balance = 0
        for p in active_players:
            value = self.game_contract.quick_read('Balances', p)
            total_player_balance += value

        in_theory_balance = len(active_players) * buy_in

        pot_size_key = 'games:' + game_id + ':pot_size'
        pot_size = self.game_contract.quick_read('S', pot_size_key)
        total_game_balance = pot_size + total_player_balance
        # print(pot_size)
        # print(type(pot_size))

        self.assertEqual(total_game_balance, in_theory_balance)

    def test_03g_joinTable(self):
        game = self.game_contract.createGame(number_of_seats = 5, ante = 5)
        game_id = game['game_id']

        self.currency_contract.approve(amount = 10000, to = 'con_azduz_master')
        self.game_contract.addFunds(amount = 10000)

        players_key = 'games' + ':' + game['game_id'] + ':players'
        waiting_key = 'games' + ':' + game['game_id'] + ':waiting'
        sitting_out_key = 'games' + ':' + game['game_id'] + ':sitting_out'
        pot_size_key = 'games' + ':' + game['game_id'] + ':pot_size'
    
        buy_in = 80

        self.game_contract.transferFunds(signer = "sys", amount = buy_in, to = 'benji')
        self.game_contract.transferFunds(signer = "sys", amount = buy_in, to = 'mick')
        self.game_contract.transferFunds(signer = "sys", amount = buy_in, to = 'julia')        
        self.game_contract.transferFunds(signer = "sys", amount = buy_in, to = 'fred')
        self.game_contract.transferFunds(signer = "sys", amount = buy_in, to = 'mona')

        # Players benji + mick sit down and a round begins

        self.game_contract.joinTable(signer = 'benji', game_id = game_id)
        self.game_contract.joinTable(signer = 'mick', game_id = game_id)

        self.game_contract.dealHand(signer = 'benji', game_id = game_id)
        self.game_contract.dealDecisionCard(game_id = game_id, amount = 4, signer='benji')
        self.game_contract.dealHand(signer = 'benji', game_id = game_id)
        self.game_contract.joinTable(signer = 'mona', game_id = game_id)
        self.game_contract.dealDecisionCard(game_id = game_id, amount = 4, signer='mick')
        
        self.game_contract.decideStartRound(game_id = game_id)
        self.game_contract.dealHand(signer = 'benji', game_id = game_id)
        self.game_contract.dealDecisionCard(game_id = game_id, amount = 4, signer='benji')
        self.game_contract.dealHand(signer = 'benji', game_id = game_id)
        self.game_contract.dealDecisionCard(game_id = game_id, amount = 4, signer='mick')
        self.game_contract.dealHand(signer = 'benji', game_id = game_id)
        self.game_contract.dealDecisionCard(game_id = game_id, amount = 4, signer='mona')

        self.game_contract.decideStartRound(game_id = game_id)
        self.game_contract.dealHand(signer = 'benji', game_id = game_id)
        self.game_contract.dealDecisionCard(game_id = game_id, amount = 4, signer='benji')
        self.game_contract.dealHand(signer = 'benji', game_id = game_id)
        self.game_contract.dealDecisionCard(game_id = game_id, amount = 4, signer='mick')
        self.game_contract.dealHand(signer = 'benji', game_id = game_id)
        self.game_contract.dealDecisionCard(game_id = game_id, amount = 4, signer='mona')

        bal_benji = self.game_contract.quick_read('Balances', 'benji')
        bal_mona = self.game_contract.quick_read('Balances', 'mona')
        bal_mick = self.game_contract.quick_read('Balances', 'mick')
        bal_pot = self.game_contract.quick_read('S', pot_size_key)

        print(bal_benji)
        print(bal_mona)
        print(bal_mick)
        print(bal_pot)

        players = self.game_contract.quick_read('S', players_key)
        waiting = self.game_contract.quick_read('S', waiting_key)
        sitting_out = self.game_contract.quick_read('S', sitting_out_key)

        active_players = self.game_contract.getActivePlayers(players = players, sitting_out = sitting_out, waiting = waiting)
        total_player_balance = 0
        for p in active_players:
            value = self.game_contract.quick_read('Balances', p)
            total_player_balance += value

        in_theory_balance = len(active_players) * buy_in

        pot_size_key = 'games:' + game_id + ':pot_size'
        pot_size = self.game_contract.quick_read('S', pot_size_key)
        total_game_balance = pot_size + total_player_balance

        self.assertEqual(total_game_balance, in_theory_balance)

    def test_03h_joinTable(self):
        game = self.game_contract.createGame(number_of_seats = 5, ante = 5)
        game_id = game['game_id']

        self.currency_contract.approve(amount = 10000, to = 'con_azduz_master')
        self.game_contract.addFunds(amount = 10000)

        players_key = 'games' + ':' + game['game_id'] + ':players'
        waiting_key = 'games' + ':' + game['game_id'] + ':waiting'
        sitting_out_key = 'games' + ':' + game['game_id'] + ':sitting_out'
        pot_size_key = 'games' + ':' + game['game_id'] + ':pot_size'
    
        buy_in = 80

        self.game_contract.transferFunds(signer = "sys", amount = buy_in, to = 'benji')
        self.game_contract.transferFunds(signer = "sys", amount = buy_in, to = 'mick')
        self.game_contract.transferFunds(signer = "sys", amount = buy_in, to = 'julia')        
        self.game_contract.transferFunds(signer = "sys", amount = buy_in, to = 'fred')
        self.game_contract.transferFunds(signer = "sys", amount = buy_in, to = 'mona')

        # Players benji + mick sit down and a round begins

        self.game_contract.joinTable(signer = 'benji', game_id = game_id)
        self.game_contract.joinTable(signer = 'mick', game_id = game_id)

        self.game_contract.dealHand(signer = 'benji', game_id = game_id)
        self.game_contract.dealDecisionCard(game_id = game_id, amount = 4, signer='benji')
        self.game_contract.dealHand(signer = 'benji', game_id = game_id)
        self.game_contract.joinTable(signer = 'mona', game_id = game_id)
        self.game_contract.joinTable(signer = 'fred', game_id = game_id)
        self.game_contract.joinTable(signer = 'julia', game_id = game_id)


        self.game_contract.dealDecisionCard(game_id = game_id, amount = 4, signer='mick')
        
        self.game_contract.decideStartRound(game_id = game_id)
        self.game_contract.dealHand(signer = 'benji', game_id = game_id)
        self.game_contract.dealDecisionCard(game_id = game_id, amount = 4, signer='benji')
        self.game_contract.dealHand(signer = 'benji', game_id = game_id)
        self.game_contract.dealDecisionCard(game_id = game_id, amount = 4, signer='mick')
        self.game_contract.dealHand(signer = 'benji', game_id = game_id)
        self.game_contract.dealDecisionCard(game_id = game_id, amount = 4, signer='mona')
        self.game_contract.dealHand(signer = 'benji', game_id = game_id)
        self.game_contract.dealDecisionCard(game_id = game_id, amount = 4, signer='fred')
        self.game_contract.dealHand(signer = 'benji', game_id = game_id)
        self.game_contract.dealDecisionCard(game_id = game_id, amount = 4, signer='julia')

        bal_benji = self.game_contract.quick_read('Balances', 'benji')
        bal_mona = self.game_contract.quick_read('Balances', 'mona')
        bal_mick = self.game_contract.quick_read('Balances', 'mick')
        bal_pot = self.game_contract.quick_read('S', pot_size_key)

        print(bal_benji)
        print(bal_mona)
        print(bal_mick)
        print(bal_pot)

        players = self.game_contract.quick_read('S', players_key)
        waiting = self.game_contract.quick_read('S', waiting_key)
        sitting_out = self.game_contract.quick_read('S', sitting_out_key)

        active_players = self.game_contract.getActivePlayers(players = players, sitting_out = sitting_out, waiting = waiting)
        total_player_balance = 0
        for p in active_players:
            value = self.game_contract.quick_read('Balances', p)
            total_player_balance += value

        in_theory_balance = len(active_players) * buy_in

        pot_size_key = 'games:' + game_id + ':pot_size'
        pot_size = self.game_contract.quick_read('S', pot_size_key)
        total_game_balance = pot_size + total_player_balance

        self.assertEqual(total_game_balance, in_theory_balance)


    def test_04a_calcDecisionCardBalance(self):
        pot_size = 4
        result = 'win'
        amount = 4
        player_balance = 4

        result = self.game_contract.calcDecisionCardBalance(
            result = result, 
            player_balance = player_balance, 
            pot_size = pot_size, 
            amount = amount
        )

        self.assertEqual(result['pot_size'], 0)
        self.assertEqual(result['player_balance'], 8)

    def test_04b_calcDecisionCardBalance(self):
        pot_size = 4
        result = 'lose'
        amount = 4
        player_balance = 4

        result = self.game_contract.calcDecisionCardBalance(
            result = result, 
            player_balance = player_balance, 
            pot_size = pot_size, 
            amount = amount
        )

        self.assertEqual(result['pot_size'], 8)
        self.assertEqual(result['player_balance'], 0)

    def test_04c_calcDecisionCardBalance(self):
        pot_size = 4
        result = 'rail'
        amount = 4
        player_balance = 8

        result = self.game_contract.calcDecisionCardBalance(
            result = result, 
            player_balance = player_balance, 
            pot_size = pot_size, 
            amount = amount
        )

        self.assertEqual(result['pot_size'], 12)
        self.assertEqual(result['player_balance'], 0)

    def test_05a_incrementPotByAntes(self):
        pot_size = 5
        ante = 5
        active_players = ['benji', 'julia', 'mick', 'fred', 'mona', 'borris']
        new_pot = self.game_contract.incrementPotByAntes(pot_size = pot_size, ante = ante, active_players = active_players)
        self.assertEqual(new_pot, 35)

    def test_05a_incrementPotByAntes(self):
        pot_size = 160
        ante = 10
        active_players = ['benji', 'julia', 'mick', 'fred', 'mona', 'borris']
        new_pot = self.game_contract.incrementPotByAntes(pot_size = pot_size, ante = ante, active_players = active_players)
        self.assertEqual(new_pot, 220)





    # Checking Balance Deductions work correctly.
    # def test_03g_joinTable(self):
    #     game = self.game_contract.createGame(number_of_seats = 5, ante = 5)
    #     game_id = game['game_id']

    #     self.currency_contract.approve(amount = 10000, to = 'con_azduz_master')
    #     self.game_contract.addFunds(amount = 10000)

    #     buy_in = 80

    #     self.game_contract.transferFunds(signer = "sys", amount = buy_in, to = 'benji')
    #     self.game_contract.transferFunds(signer = "sys", amount = buy_in, to = 'mick')

    #     # Players benji + mick sit down and a round begins

    #     self.game_contract.joinTable(signer = 'benji', game_id = game_id)
    #     self.game_contract.joinTable(signer = 'mick', game_id = game_id)

    #     self.game_contract.dealDecisionCard(game_id = game_id, amount = 4, signer='benji')
    #     self.game_contract.dealDecisionCard(game_id = game_id, amount = 4, signer='mick')
    #     self.game_contract.dealDecisionCard(game_id = game_id, amount = 4, signer='benji')
    #     self.game_contract.dealDecisionCard(game_id = game_id, amount = 4, signer='mick')
        
    #     active_players = self.game_contract.getActivePlayers(game_id = game_id)
    #     total_player_balance = 0
    #     for p in active_players:
    #         value = self.game_contract.quick_read('Balances', p)
    #         total_player_balance += value
    #     print(total_player_balance)

    #     total_in_game = len(active_players) * buy_in

    #     pot = self.game_contract.quick_read('games', game_id, 'pot_size')

    #     pot += len(active_players) * buy_in

    #     self.assertEqual(total_player_balance, total_in_game)

        # Checking Balance Deductions work correctly.
    # def test_03h_joinTable(self):
    #     game = self.game_contract.createGame(number_of_seats = 5, ante = 5)
    #     game_id = game['game_id']

    #     self.currency_contract.approve(amount = 10000, to = 'con_azduz_master')
    #     self.game_contract.addFunds(amount = 10000)

    #     buy_in = 80

    #     self.game_contract.transferFunds(signer = "sys", amount = buy_in, to = 'benji')
    #     self.game_contract.transferFunds(signer = "sys", amount = buy_in, to = 'mick')
    #     self.game_contract.transferFunds(signer = "sys", amount = buy_in, to = 'julia')        
    #     self.game_contract.transferFunds(signer = "sys", amount = buy_in, to = 'fred')
    #     self.game_contract.transferFunds(signer = "sys", amount = buy_in, to = 'mona')

    #     # Players benji + mick sit down and a round begins

    #     self.game_contract.joinTable(signer = 'benji', game_id = game_id)
    #     self.game_contract.joinTable(signer = 'mick', game_id = game_id)

    #     # self.game_contract.joinTable(signer = 'julia', game_id = game_id)
    #     # self.game_contract.joinTable(signer = 'fred', game_id = game_id)
    #     # self.game_contract.joinTable(signer = 'mona', game_id = game_id)

    #     self.game_contract.dealDecisionCard(game_id = game_id, amount = 4, signer='benji')
    #     self.game_contract.dealDecisionCard(game_id = game_id, amount = 4, signer='mick')
        
    #     active_players = self.game_contract.getActivePlayers(game_id = game_id)
    #     total_player_balance = 0
    #     for p in active_players:
    #         value = self.game_contract.quick_read('Balances', p)
    #         total_player_balance += value
    #     print(total_player_balance)

    #     total_in_game = len(active_players) * buy_in

    #     self.assertEqual(total_player_balance, total_in_game)


    #     # self.game_contract.dealDecisionCard(game_id = game_id, amount = 4, signer='benji')
    #     # self.game_contract.dealDecisionCard(game_id = game_id, amount = 4, signer='mick')
    #     # self.game_contract.dealDecisionCard(signer = 'julia', game_id = game_id, amount = 4)
    #     # self.game_contract.dealDecisionCard(signer='fred', game_id = game_id, amount = 4)
    #     # self.game_contract.dealDecisionCard(signer='mona', game_id = game_id, amount = 4)

    #     # players = self.game_contract.getActivePlayers(game_id = game_id)
    #     # total_balance = 0
    #     # for p in players:
    #     #     value = self.game_contract.quick_read('Balances', p)
    #     #     total_balance += value
    #     # print(total_balance)
    #     # bal_benji = self.game_contract.quick_read('Balances', 'benji')
    #     # bal_julia = self.game_contract.quick_read('Balances', 'julia')
    #     # bal_mick = self.game_contract.quick_read('Balances', 'mick')
    #     # bal_fred = self.game_contract.quick_read('Balances', 'fred')
    #     # bal_mona = self.game_contract.quick_read('Balances', 'mona')

    #     # print(balances)




if __name__ == '__main__':
    unittest.main()