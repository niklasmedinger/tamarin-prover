import requests
import json

ENCODING = "utf-8"


class TamarinClient:
    # Ip -> Port -> Route
    server_overview_route = "http://{}:{}"
    # Ip -> Port -> TheoryKind -> TheoryIdx -> Route
    theory_overview_route = "http://{}:{}/thy/{}/{}/overview/help"
    # Ip -> Port -> TheoryKind -> TheoryIdx -> LemmaName -> ProofPath -> Route
    proof_state_route = "http://{}:{}/thy/{}/{}/overview/proof/{}{}"
    # Ip -> Port -> TheoryKind -> TheoryIdx -> LemmaName -> ProofMethodIndex
    # ProofPath -> Route
    # The proof method index refers to the index of the chosen proof method in the list of
    # proof methods one can obtain by using the proof_state_route
    main_method_route = "http://{}:{}/thy/{}/{}/main/method/{}/{}{}"

    def __init__(self, ip_addr="127.0.0.1", port="3001"):
        self.ip_addr = ip_addr
        self.port = port

    """
    Gets an overview of the loaded protocol models, called theories, of the
    interactive Tamarin server.

    Returns a JSON with the following schema:
    { String: [ { 'theoryIndex': Int, 'theoryKind': ('trace' | 'diff'), 'theoryName': String } ] }

    where the strings used as index are the names of the loaded theories.
    NOTE: that this is not the name of the `.spthy` file. It is the name of the
    model inside of the file!

    Each entry in the JSON array corresponds to a protocol model. The 'theoryIndex'
    is used for index access to the model, the 'theoryKind' defines whether
    the model deals with trace or observational equivalence properties, and
    the 'theoryName' is the user-chosen name of the theory.
    """

    def get_server_overview(self):
        return requests.get(self.server_overview_route.format(self.ip_addr, self.port))

    """
    Gets an overview of the theory status.

    Returns a JSON with the following schema:
    { 'theoryRaw': String -- The raw string of the theory
    , 'lemmas': [ Lemma ] -- The list of lemmas
    }

    where

    Lemma = { 'name': String                                -- The name of the lemma
            , 'proofState': Proof                           -- The (partial) proof of the lemma
            , 'quantifier': ('AllTraces' | 'ExistsTrace') } -- The quantifier of the lemma
    Proof = { 'cases': [ Proof ]
            , 'chosenProofMethod': String
            , 'proofStatus': (IncompleteProof | CompleteProof
                             | TraceFound | InvalidatedProof
                             | UnfinishableProof | UndeterminedProof)
            , 'constraintSystem': String
            , 'proofMethods': [ String ]
            }
    """

    def get_theory_overview(self, theory_kind, theory_index):
        return requests.get(
            self.theory_overview_route.format(
                self.ip_addr, self.port, theory_kind, theory_index
            )
        )

    """
    Gets a view of the proof state at a given proof path.

    Returns a JSON with the following schema:
    { 'proofState': Proof } -- The state of the proof
    """

    def get_proof_state(self, theory_kind, theory_index, lemma, proof_path=[]):
        proof_path = "/".join(proof_path)
        # If path is NOT empty, we need to prepend a '/'.
        # Example route: ``http://127.0.0.1:3001/thy/trace/25/overview/proof/ExtractData_Executable/_/Create_Initiator''
        if len(proof_path) > 0:
            proof_path = "/" + proof_path

        # If the path is empty, we MUST NOT have a trailing '/'; otherwise the
        # route is not correct.
        # Example route: ``http://127.0.0.1:3001/thy/trace/25/overview/proof/ExtractData_Executable''
        route = self.proof_state_route.format(
            self.ip_addr, self.port, theory_kind, theory_index, lemma, proof_path
        )
        return requests.get(route)

    """
    Applies a proof method at a given lemma and proof path. Can fail.

    If successful, it returns a JSON with the following schema:
    { 'newTheoryIndex': Int, 'nextProofpath': [ String ] }

    Here, the 'newTheoryIndex' is the new index which should be used to index
    the modified theory. Tamarin internally constructs a new theory when an
    existing theory is modified.

    The 'nextProofpath' is the path which Tamarin would have choosen if the
    path was clicked in the GUI. E.g., if multiple case distinction arise from
    the chosen proof method, it chooses the first one.

    TODO: Think about also returning the new cases here such that one
    can choose a different case.
    """

    def apply_method_at_path(
        self, theory_kind, theory_index, lemma, proof_method_index, proof_path=[]
    ):
        proof_path = "/".join(proof_path)
        # An empty proof path means we want to apply the chosen proof method
        # at the root of the proof tree.
        # Therefore, we completely omit the proof path from the route
        # Example route: "http://127.0.0.1:3001/thy/trace/1/main/method/ExtractData_Executable/1"
        if len(proof_path) > 0:
            # If the proof path is not empty, we apply the method at the path.
            # Therefore, we need to prepend a '/'.
            # Tamarin uses '_' to indicate that there is only single case
            # distinction at this node in the proof tree. We expect this to be
            # in the proof path as a string. E.g., path = ["_", "Create_Initiator"]
            # for the following example route.
            # Example route: "http://127.0.0.1:3001/thy/trace/1/main/method/ExtractData_Executable/1/_/Create_Initiator"
            proof_path = "/" + proof_path

        route = self.main_method_route.format(
            self.ip_addr,
            self.port,
            theory_kind,
            theory_index,
            lemma,
            proof_method_index,
            proof_path,
        )
        return requests.get(route)
