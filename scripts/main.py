#!/usr/bin/env python

import client
import json

if __name__ == "__main__":
    c = client.TamarinClient()
    r = c.get_server_overview()
    r = json.loads(r.text)
    theory = r["theories"][0]
    theory_kind = theory["theoryKind"]
    index = theory["index"]
    r = c.get_theory_overview(theory_kind=theory_kind, index=index)
    r = json.loads(r.text)
    lname = r["lemmas"][0]["name"]
    print(lname)
    r = c.get_proof_state(theory_kind, index, lname)
    print(r.text)
