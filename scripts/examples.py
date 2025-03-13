#!/usr/bin/env python

from client import *
import json
import random


def overview():
    # Create the client
    c = TamarinClient()
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
    theory_kind = theory[THEORY_KIND]
    theory_index = theory[THEORY_INDEX]
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
    for lemma in r[LEMMAS]:
        # Inspect name and the quantifier of the lemmas, i.e., all-traces or exists-trace
        print("Lemma: " + lemma[LEMMA_NAME] + " --- " + lemma[QUANTIFIER])

        # Inspect the proof state of the lemmas
        # This JSON contains all proof paths and, at for each path, the constraint
        # system, the ranked proof methods, and the chosen proof method etc.
        # For more details see the documentation of the client.
        # As a result, this JSON also gets huge and should not be viewed in its whole.
        proof_state = lemma[PROOF_STATE]
        print("Chosen proof method: " + proof_state[CHOSEN_PROOF_METHOD])
        print("Ranked proof methods: " + str(proof_state[PROOF_METHODS]))


def proof_state():
    # We will now take a look at how we can use the client to apply proof
    # methods and how the proof state JSON looks like.

    # Setup as before
    c = TamarinClient()
    r = c.get_server_overview()
    r = json.loads(r.text)
    # Choose a theory from the response
    theory = r["Tutorial"]
    # The index and kind of theory are needed by Tamarin to index it internally
    theory_kind = theory[THEORY_KIND]
    theory_index = theory[THEORY_INDEX]
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
    # to the name of a case in a case distinction. If there is only a single
    # case, the "_" is used to `select' it.

    # Let's prove something now!
    # `proof_path` will be the current path we are focusing on.
    proof_path = []

    # Get the proof state
    proof_state = json.loads(
        c.get_proof_state(theory_kind, theory_index, lemma_name, proof_path).text
    )
    proof_methods = proof_state[PROOF_METHODS]
    # Inspect the ranked methods
    # print(proof_methods)

    # Let's take a look at how we can apply a proof method!

    # Not specifying `proof_path` for this function defaults to `[]`.
    # Thus, we could have ommitted it in this case since `proof_path` = [] currently.
    r = c.apply_method_at_path(theory_kind, theory_index, lemma_name, 1, proof_path)
    # `apply_method_at_path` applies the method at index `1` at proof path [] of
    # the lemma. The index refers to the method at the corresponding proof
    # methods list. I.e., we choose `proof_methods[1]`

    # This method can fail if the path is invalid or the lemma does not exist
    if r.ok:
        r = json.loads(r.text)
    else:
        raise ValueError("Invalid proof path: " + str(proof_path))

    # The response JSON for applying a proof method looks like this:
    # { 'newTheoryIndex': Int, 'nextProofpath': Optional [ String ] }

    # If not 'None', the 'nextProofpath' list is the path to the next case in
    # the proof Tamarin wants to focus on. Currently, Tamarin simply iterates
    # through case distinctions in order.
    # If 'None', this indicates that the proof for this lemma is finished.

    # The 'newTheoryIndex' is the index to the new theory that contains the
    # new, modified proof state. Internally, Tamarin creates a new theory
    # everytime an existing theory is modified. Thus, we have to deal with this.

    theory_index = r[NEW_THEORY_INDEX]
    proof_path = r[NEXT_PROOF_PATH]

    # Now we can inspect the new proof state and continue

    r = c.get_proof_state(theory_kind, theory_index, lemma_name, proof_path)

    # Proof paths returned by Tamarin are always valid paths
    # If not, that's a bug in the server or client code
    r = json.loads(r.text)

    proof_methods = r[PROOF_METHODS]
    print(proof_methods)

    # Continue the proof from here...


def proving():
    # We will now take a look at how we can use the client to prove a lemma

    # Setup as before
    c = TamarinClient()
    r = c.get_server_overview()
    r = json.loads(r.text)
    theory = r["Tutorial"]
    theory_kind = theory[THEORY_KIND]
    theory_index = theory[THEORY_INDEX]
    lemma_name = "Client_session_key_secrecy"

    # We can define a custom function for ranking proof methods
    def custom_heuristic(proof_methods):
        # proof methods indices are 1-based.
        return random.randrange(1, len(proof_methods) + 1)

    # Setup variables needed for proving
    r = c.get_proof_state(theory_kind, theory_index, lemma_name)
    proof_state = json.loads(r.text)
    method_index = custom_heuristic(proof_state[PROOF_METHODS])
    proof_path = []

    # Apply proof methods until proof is finished
    while True:
        r = c.apply_method_at_path(
            theory_kind, theory_index, lemma_name, method_index, proof_path
        )
        # Assuming everything goes right
        r = json.loads(r.text)
        theory_index = r[NEW_THEORY_INDEX]
        proof_path = r[NEXT_PROOF_PATH]
        if proof_path is None:
            break
        else:
            # Warning: You should always give a proof path when querying for the
            # proof state in a hot loop. The reason is that the resulting
            # JSON grows exponentially in size in the number of proof steps
            # because it contains the whole proof tree
            proof_state = json.loads(
                c.get_proof_state(
                    theory_kind, theory_index, lemma_name, proof_path
                ).text
            )

    r = c.get_proof_state(theory_kind, theory_index, lemma_name)
    r = json.loads(r.text)
    print(r[PROOF_STATUS])


if __name__ == "__main__":
    # The examples assume that you have a modified Tamarin server running
    # at the default address

    # Shows basic commands, e.g., getting information about the loaded
    # theories and their lemmas
    overview()

    # Shows how the proof state works and how you can apply prove methods
    # proof_state()

    # Proving whole statements
    # proving()
