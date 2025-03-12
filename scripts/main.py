#!/usr/bin/env python

import client
import json


def overview():
    # Create the client
    c = client.TamarinClient()
    # Ip and port can be changed
    # c = client.TamarinClient(ip_addr="127.0.0.2", port="3002")

    # Get an overview of the server. This is the initial list of models
    # you will see when opening the GUI of the interactive mode.
    # See the documentation of the client for the exact format of the JSON.
    r = c.get_server_overview()
    # Load the json from the request (assuming its a good response)
    r = json.loads(r.text)
    # print("==========================================================================")
    # print("# The server overview")
    # print(r)

    # Choose a theory from the response
    theory = r["Tutorial"]
    # The index and kind of theory are needed by Tamarin to index it internally
    theory_kind = theory["theoryKind"]
    theory_index = theory["theoryIndex"]
    # Get an overview of the theory.
    r = c.get_theory_overview(theory_kind, theory_index)
    r = json.loads(r.text)
    # The theory overview contains all the lemmas and their proof states.
    # This JSON gets huge! Thus, viewing it in its whole does not make much sense.
    # See the documentation of of the client for the exact JSON format.
    # print("==========================================================================")
    # print("# The theory overview")
    # print(r)

    # Inspect the lemmas
    for lemma in r["lemmas"]:
        # Inspect name and the quantifier of the lemmas, i.e., all-traces or exists-trace
        print("Lemma: " + lemma["name"] + " --- " + lemma["quantifier"])

        # Inspect the proof state of the lemmas
        # This JSON contains all proof paths and, at for each path, the constraint
        # system, the ranked proof methods, and the chosen proof method etc.
        # For more details see the documentation of the client.
        # As a result, this JSON also gets huge and should not be viewed in its whole.
        proof_state = lemma["proofState"]
        print("Chosen proof method: " + proof_state["chosenProofMethod"])
        print("Ranked proof methods: " + str(proof_state["proofMethods"]))


def proof_state():
    # We will now take a look at how we can use the client to prove a lemma

    # Setup as before
    c = client.TamarinClient()
    r = c.get_server_overview()
    r = json.loads(r.text)
    # Choose a theory from the response
    theory = r["Tutorial"]
    # The index and kind of theory are needed by Tamarin to index it internally
    theory_kind = theory["theoryKind"]
    theory_index = theory["theoryIndex"]
    # Suppose we know that the file contains the lemma "Client_session_key_secrecy"
    lemma_name = "Client_session_key_secrecy"
    # We can get the proof state of a specific lemma at the root of the proof tree
    valid_proof_state = c.get_proof_state(theory_kind, theory_index, lemma_name)
    # We can also get the proof state at a specific path of the proof
    invalid_proof_state = c.get_proof_state(
        theory_kind, theory_index, lemma_name, proof_path=["Non", "existing", "path"]
    )
    # Since this path does not exist, the response will have error code 400
    # The easiest way to check for this is to use the `.ok` field of the response
    # object
    # print(
    #     "Valid proof path: " + str(valid_proof_state.ok),
    #     "---",
    #     "Invalid proof path: " + str(invalid_proof_state.ok),
    # )

    # A proof path is just a list of strings. In Tamarin, each string corresponds
    # to the name of a case in a case distinctions. If there is only a single
    # case, the "_" is used to `select' it.

    # Let's prove something now!
    # `proof_path` will be the current path we are focusing on.
    proof_path = []

    # Get the proof state
    proof_state = json.loads(
        c.get_proof_state(theory_kind, theory_index, lemma_name, proof_path).text
    )
    proof_methods = proof_state["proofMethods"]
    # Inspect the ranked methods
    # print(proof_methods)

    # Let's take a look at how we can apply a proof method!

    # Applies the method at index `1` at proof path [] of the lemma
    # The index refers to the method at the corresponding proof methods list
    # I.e., we choose `proof_methods[1]`
    r = c.apply_method_at_path(theory_kind, theory_index, lemma_name, 1)

    # for _ in range(0, 50):
    #     # Always choose the first proof method
    #     r = c.apply_method_at_path(theory_kind, index, lname, 1, proof_path)
    #     print("=========================")
    #     print(r.text)
    #     print("=========================")
    #     res = json.loads(r.text)
    #     index = res["newTheoryIndex"]
    #     proof_path = res["nextProofpath"]
    #     proof_state = c.get_proof_state(theory_kind, index, lname, proof_path)


if __name__ == "__main__":
    # The examples assume that you have a modified Tamarin server running
    # at the default address

    # Shows basic commands, e.g., getting information about the loaded
    # theories and their lemmas
    # overview()

    # Shows how the proof state works and how you can apply prove methods
    proof_state()

    # Proving whole statements
    # proving()
