# -*- coding: utf-8 -*-
"""Aplicație Streamlit – Algebră booleană (ASDN, Lucrările 1, 2 și 3). Rulare: streamlit run app.py"""
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from boolean_core import (parse_functie, EroareSintaxa, variables, ltx, sstr, simplifica, echivalent, LEGI,
                          tabel_cols, forme_canonice, cod_matlab, cod_simulink, pas_eval, ev)
from circuit_draw import deseneaza

st.set_page_config(page_title="Algebră Booleană", page_icon="🔌", layout="centered")
st.title("🔌 Algebră Booleană")

with st.sidebar:
    st.header("Ghid de scriere")
    st.markdown(
        "- **ȘI:** `×  *  ·  &  AND  ȘI` sau lipit (`AB`)\n"
        "- **SAU:** `+  |  OR  SAU`\n"
        "- **NU:** `A'  !A  ~A  NOT A  NU A` sau `A̅`\n"
        "- **XOR:** `⊕  ^  XOR`\n"
        "- Constante `0` și `1`, paranteze `( )`\n"
        "- Prioritate: NU > ȘI > XOR > SAU\n\n"
        "Exemple: `F = A×B + A`, `D = !(A'B + C')(A+C)`, `Y = A ⊕ B`")
    with st.expander("Proprietăți (Lucrarea 1)"):
        for k in ['com', 'dist_exp', 'idem_or', 'idem_and', 'dn', 'abs_or', 'abs_and', 'reu_or', 'reu_and',
                  'int_or', 'int_and', 'comp_or', 'comp_and', 'dm_and', 'dm_or']:
            st.markdown(f"**{LEGI[k][0]}:** ${LEGI[k][1]}$")


def citeste(text):
    try:
        return parse_functie(text)
    except EroareSintaxa as ex:
        st.error(f"⚠️ {ex}")
        return None


def schema(e, nume, titlu):
    st.markdown(f"**{titlu}**")
    fig = deseneaza(e, nume)
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)
    st.caption("Intrările care se repetă sunt desenate separat, pentru claritate.")


t1, t2 = st.tabs(["1️⃣ Simplificare", "2️⃣ Evaluare cu valori"])

# ======================= TAB 1 =======================
with t1:
    r = citeste(st.text_input("Funcția logică", "F = A×B + A", key="f1"))
    if r:
        nume, e = r
        vs = sorted(variables(e))
        st.latex(f"{nume} = {ltx(e)}")
        pasi, fin = simplifica(e)

        st.subheader("Pașii de rezolvare")
        if not pasi:
            st.info("Expresia este deja în forma cea mai simplă – nu se mai poate aplica nicio proprietate.")
        for k, (lege, ex) in enumerate(pasi, 1):
            st.markdown(f"**{k}. {LEGI[lege][0]}** &nbsp; ${LEGI[lege][1]}$")
            st.latex(f"{nume} = {ltx(ex)}")
        st.success("Rezultat final")
        st.latex(f"{nume} = {ltx(fin)}")
        if echivalent(e, fin):
            st.caption("✔️ Verificat: expresia inițială și cea simplificată au aceeași tabelă de adevăr.")

        st.subheader("Tabela de adevăr")
        interm = st.checkbox("Arată coloanele intermediare", True, key="i1")
        st.dataframe(pd.DataFrame(tabel_cols(e, vs, nume, interm)), hide_index=True, use_container_width=True)

        if vs:
            mi, Ma, s1, s2 = forme_canonice(e, vs)
            with st.expander("Forme canonice (Lucrarea 2_3)"):
                st.markdown("**FCND – sumă de mintermi**")
                st.latex(rf"{nume}=\sum m({','.join(map(str, mi))}) = {s1}")
                st.markdown("**FCNC – produs de maxtermi**")
                st.latex(rf"{nume}=\prod M({','.join(map(str, Ma))}) = {s2}")

        st.subheader("Schema cu porți logice")
        schema(e, nume, "Funcția inițială")
        if fin != e:
            schema(fin, nume, "Funcția simplificată")

        st.subheader("Cod MATLAB")
        m1, m2 = cod_matlab(nume, fin, vs), cod_simulink(nume, fin, vs)
        a, b = st.tabs(["Script MATLAB", "Model Simulink"])
        with a:
            st.caption("Codul este pentru funcția simplificată.")
            st.code(m1, language="matlab")
            st.download_button("⬇️ Descarcă .m", m1, f"{nume}_script.m", key="d1")
        with b:
            st.caption("Rulați scriptul în MATLAB: creează automat schema cu porți și blocul Display.")
            st.code(m2, language="matlab")
            st.download_button("⬇️ Descarcă .m", m2, f"{nume}_simulink.m", key="d2")

# ======================= TAB 2 =======================
with t2:
    r = citeste(st.text_input("Funcția logică", "F = A×B + A", key="f2"))
    if r:
        nume, e = r
        vs = sorted(variables(e))
        st.latex(f"{nume} = {ltx(e)}")
        st.markdown("**Valorile variabilelor**")
        val = {}
        cols = st.columns(min(max(len(vs), 1), 4))
        for i, v in enumerate(vs):
            val[v] = cols[i % len(cols)].radio(v, [0, 1], horizontal=True, key=f"val_{v}")

        st.subheader("Calcul pas cu pas")
        st.markdown("Se înlocuiesc variabilele și se evaluează de la interior spre exterior:")
        for x in pas_eval(e, val):
            st.latex(f"{nume} = {ltx(x)}")
        rez = ev(e, val)
        st.metric(f"{nume}(" + ", ".join(f"{v}={val[v]}" for v in vs) + ")", rez)

        st.subheader("Tabela de adevăr")
        df = pd.DataFrame(tabel_cols(e, vs, nume, st.checkbox("Arată coloanele intermediare", True, key="i2")))
        idx = int("".join(str(val[v]) for v in vs) or "0", 2)
        st.dataframe(df.style.apply(lambda row: ["background-color:#ffe08a;color:#000" if row.name == idx else ""] * len(row), axis=1),
                     hide_index=True, use_container_width=True)
        st.caption("Rândul evidențiat corespunde valorilor alese.")
        schema(e, nume, "Schema cu porți logice")
