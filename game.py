from copy import deepcopy

from easyAI import TwoPlayerGame, Human_Player, AI_Player, Negamax, NonRecursiveNegamax
import random
import time

from easyAI import TwoPlayerGame

from ExpectiMinimax import ExpectiMinimax

# Convert D7 to (3,6) and back...
to_string = lambda move: " ".join(
    ["ABCDEFGHIJ"[move[i][0]] + str(move[i][1] + 1) for i in (0, 1)]
)
to_tuple = lambda s: ("ABCDEFGHIJ".index(s[0]), int(s[1:]) - 1)


class Octospawn(TwoPlayerGame):
    """
    A nice game whose rules are explained here:
    http://fr.wikipedia.org/wiki/Hexapawn
    """

    def __init__(self, players, size=(4, 4), with_respawns=False, average_time_file=None, winner_file=None):
        self.size = M, N = size
        p = [[(i, j) for j in range(N)] for i in [0, M - 1]]

        for i, d, goal, pawns in [(0, 1, M - 1, p[0]), (1, -1, 0, p[1])]:
            players[i].direction = d
            players[i].goal_line = goal
            players[i].pawns = pawns
            players[i].starting_pawns = list(pawns)

        self.players = players
        self.current_player = 1

        self.history_of_moves = []

        self.with_respawns = with_respawns

        self.place_to_respawn = {
            1 : [],
            2 : []
        }

        if average_time_file is None:
            average_time_file = "average_time_file.txt"
        self.average_time_file = average_time_file

        if winner_file is None:
            winner_file = "winner_file.txt"
        self.winner_file = winner_file

        self.last_move_time = time.time()

        with open(average_time_file, "w") as f:
            f.write("")
        with open(winner_file, "w") as f:
            f.write("")

    def toogle_timer(self):
        start = self.last_move_time
        self.last_move_time = time.time()

        with open(self.average_time_file, "a") as f:
            f.write(f'{self.current_player}, {self.last_move_time - start}\n')

    def possible_moves(self):
        moves = []
        opponent_pawns = self.opponent.pawns
        d = self.player.direction
        for i, j in self.player.pawns:
            if (i + d, j) not in opponent_pawns:
                moves.append(((i, j), (i + d, j)))
            if (i + d, j + 1) in opponent_pawns:
                moves.append(((i, j), (i + d, j + 1)))
            if (i + d, j - 1) in opponent_pawns:
                moves.append(((i, j), (i + d, j - 1)))

        return list(map(to_string, [(i, j) for i, j in moves]))

    def make_move(self, move):
        move = list(map(to_tuple, move.split(" ")))
        ind = self.player.pawns.index(move[0])
        self.player.pawns[ind] = move[1]

        self.history_of_moves.append((self.current_player, move[0], move[1]))

        if move[1] in self.opponent.pawns:
            self.opponent.pawns.remove(move[1])
            if self.with_respawns:
                opponent = 2 if self.current_player == 1 else 1
                self.place_to_respawn[opponent].append(self.add_respawn(move[1],opponent))

        self.respawn_pawn()

    def add_respawn(self, target_move, opponent):
        """Dodaje pierwotne miejsce zbitego pionka do listy respawnów"""
        target = target_move
        for player, start, end in reversed(self.history_of_moves):
            if end == target_move and player == opponent:
                target = self.add_respawn(start, opponent)
                break

        return target

    def respawn_pawn(self):
        """10% szansy na odrodzenie pionka na pierwotnej pozycji."""
        if self.with_respawns and random.random() < 0.1 and self.place_to_respawn[self.current_player]:
            respawn_position = random.choice(self.place_to_respawn[self.current_player])
            if respawn_position not in self.player.pawns:
                self.player.pawns.append(respawn_position)
            self.place_to_respawn[self.current_player].remove(respawn_position)

    def lose(self):
        return any([i == self.opponent.goal_line for i, j in self.opponent.pawns]) or (
                self.possible_moves() == []
        )

    def is_over(self):
        return self.lose()

    def show(self):
        f = (
            lambda x: "1"
            if x in self.players[0].pawns
            else ("2" if x in self.players[1].pawns else ".")
        )
        print(
            "\n".join(
                [
                    " ".join([f((i, j)) for j in range(self.size[1])])
                    for i in range(self.size[0])
                ]
            )
        )

    def ttentry(self):
        """ Hashuje aktualny stan gry dla pamięci transpozycyjnej. """
        return tuple(sorted(self.players[0].pawns)), tuple(sorted(self.players[1].pawns))

    def ttrestore(self, entry):
        """ Przywraca stan gry na podstawie pamięci transpozycyjnej. """
        self.players[0].pawns, self.players[1].pawns = list(entry[0]), list(entry[1])

    def play(self, nmoves=1000, verbose=True):
        history = []

        if verbose:
            self.show()

        for self.nmove in range(1, nmoves + 1):

            if self.is_over():
                with open(self.winner_file, "w") as f:
                    f.write(str(self.opponent_index))
                break

            move = self.player.ask_move(self)
            history.append((deepcopy(self), move))
            self.make_move(move)

            if verbose:
                print(
                    "\nMove #%d: player %d plays %s :"
                    % (self.nmove, self.current_player, str(move))
                )
                self.show()
            self.toogle_timer()
            self.switch_player()

        history.append(deepcopy(self))

        return history


if __name__ == "__main__":
    scoring = lambda game: -100 if game.lose() else 0
    ai1 = Negamax(10, scoring) #z alpha-beta
    ai2 = ExpectiMinimax(12, scoring) #bez alpha-beta
    game = Octospawn([AI_Player(ai1), AI_Player(ai2)],with_respawns=True,average_time_file="average_time_file.txt",winner_file="resutl.txt")
    game.play()
    print("player %d wins after %d turns " % (game.opponent_index, game.nmove))
