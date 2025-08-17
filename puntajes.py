import streamlit as st
import random

st.set_page_config(
    page_title='Puntajes',
    layout="wide",
)

st.title("Torneo Galadhrym", anchor=False)

# Inputs
col01, col02 = st.columns(2)
with col01:
    rounds = st.number_input("Número de Sets", 3, 11, 3, 2)
with col02:
    playerN = st.number_input("Número de Jugadores", 2, 64, 4, 1)

# Player names
players = []

col1, col2 = st.columns(2)  # Create 2 columns

for i in range(playerN):
    # Alternate between columns
    col = col1 if i % 2 == 0 else col2
    name = col.text_input(f"Nombre Jugador {i+1}", value=f"Jugador {i+1}", key=f"player_{i}")
    if name:
        players.append(name)

# ---------- Match helper ----------
def play_match(p1, p2, rounds, match_key):
    """Render a match and return (winner, loser) or (None, None) if unresolved."""
    if p2 is None:
        st.info(f"{p1} avanza automáticamente por bye")
        return p1, None

    st.markdown(f"### {p1} 🆚 {p2}")
    cols = st.columns(rounds)

    p1_wins = 0
    p2_wins = 0
    target_wins = (rounds // 2) + 1

    for r in range(rounds):
        # Stop if someone already reached target wins
        finished = (p1_wins >= target_wins or p2_wins >= target_wins)

        with cols[r]:
            s1 = st.number_input(
                f"{p1} - Set {r+1}",
                min_value=0,
                max_value=100,
                value=0,
                key=f"{match_key}_s{r}_p1",
                disabled=finished
            )
            s2 = st.number_input(
                f"{p2} - Set {r+1}",
                min_value=0,
                max_value=100,
                value=0,
                key=f"{match_key}_s{r}_p2",
                disabled=finished
            )

        if not finished:
            if s1 > s2:
                p1_wins += 1
            elif s2 > s1:
                p2_wins += 1


    # Decide winner only if target_wins reached
    if p1_wins >= target_wins:
        winner, loser = p1, p2
    elif p2_wins >= target_wins:
        winner, loser = p2, p1
    else:
        winner, loser = "Empate", "Empate"

    if winner != "Empate":
        st.success(f"Ganador: {winner}")
    else:
        st.warning("Duelo Empatado")

    return winner, loser



def sortear(players):
    shuffled = players.copy()
    random.shuffle(shuffled)
    st.session_state["seeded_players"] = shuffled
    return shuffled


# ---------- Tournament ----------
if len(players) == playerN:
    #shuffled = sortear(players)
    # Sorteo sólo fija el orden inicial (semilla). Todo lo demás se recalcula limpio en cada rerun.
    if st.button("🎲 Sortear enfrentamientos", type="primary"):
        shuffled = sortear(players)

    seeded = st.session_state.get("seeded_players", None)
    if seeded:
        # ===== Winners bracket =====
        winners_round = seeded[:]   # working list
        all_losers_pre_final = []   # losers from winner rounds EXCEPT the final
        final_loser = None          # runner-up (2º lugar)
        match_counter = 0
        round_num = 1
        unresolved = False

        while len(winners_round) > 1:
            st.subheader(f"Ronda {round_num} - Cuadro de Ganadores")
            next_round = []
            temp = winners_round[:]  # copy

            # Bye if odd
            if len(temp) % 2 == 1:
                bye = temp.pop()
                st.info(f"{bye} recibe un bye (ganadores)")
                next_round.append(bye)

            is_final_round = (len(winners_round) == 2)

            # Pair sequentially for determinism
            while temp:
                p1 = temp.pop(0)
                p2 = temp.pop(0) if temp else None
                match_counter += 1
                w, l = play_match(p1, p2, rounds, f"W_r{round_num}_m{match_counter}")
                if w == "Empate":
                    unresolved = True
                    continue
                next_round.append(w)
                if l:
                    if is_final_round:
                        # Final loser = 2º lugar (no va al cuadro de perdedores)
                        final_loser = l
                    else:
                        all_losers_pre_final.append(l)

            winners_round = next_round
            round_num += 1

        # Champion
        champion = winners_round[0] if winners_round else None

        # ===== Losers (classification) bracket =====
        # Only losers from rounds before the final:
        losers_pool = all_losers_pre_final[:]
        eliminated_order = []  # from worst (eliminated earliest here) to near-best

        lround = 1
        while len(losers_pool) > 1:
            st.subheader(f"Ronda {round_num} - Cuadro de Perdedores")
            next_pool = []
            tmp = losers_pool[:]

            if len(tmp) % 2 == 1:
                bye = tmp.pop()
                st.info(f"{bye} recibe un bye (perdedores)")
                next_pool.append(bye)

            while tmp:
                p1 = tmp.pop(0)
                p2 = tmp.pop(0) if tmp else None
                match_counter += 1
                w, l = play_match(p1, p2, rounds, f"L_r{round_num}_m{match_counter}")
                if w == "Empate":
                    unresolved = True
                    continue
                next_pool.append(w)
                if l:
                    eliminated_order.append(l)  # this player’s place is determined now

            losers_pool = next_pool
            round_num += 1

        third_place = losers_pool[0] if len(losers_pool) == 1 else None

        # ===== Build final standings (1..N) =====
        standings = []
        if champion:
            standings.append(champion)         # 1°
        if final_loser:
            standings.append(final_loser)      # 2°
        if third_place:
            standings.append(third_place)      # 3°
        # then 4°, 5°, ... from last eliminated to first eliminated in losers bracket
        standings.extend(reversed(eliminated_order))

        # Sanity: if any players weren’t placed (due to ties), tell the user.
        all_entered = set(seeded)
        placed = set([p for p in standings if p and p != "Empate"])
        missing = [p for p in seeded if p not in placed]
        if missing:
            st.warning(
                "Hay partidos sin resolver (empates). Resuelve los empates para ver la clasificación completa."
            )

        if missing == []:
            st.balloons()

            # Output
            place_emojis = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣"]
            st.header("🏆 Clasificación Final")
            for i, p in enumerate(standings):
                emoji = place_emojis[i] if i < len(place_emojis) else f"{i+1}°"
                st.write(f"{emoji} {p}")

            # Debug helpers (optional; comment out if noisy)
            # st.write("Seeded:", seeded)
            # st.write("Losers pre-final:", all_losers_pre_final)
            # st.write("Eliminated order (peor→mejor):", eliminated_order)
