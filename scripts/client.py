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
    # Ip -> Port -> TheoryKind -> TheoryIdx -> LemmaName -> ProofPath -> ProofMethodIndex -> Route
    # The proof method index refers to the index of the chosen proof method in the list of
    # proof methods one can obtain by using the proof_state_route
    main_method_route = "https://{}:{}/thy/{}/{}/main/method/{}/{}"

    def __init__(self, ip_addr="127.0.0.1", port="3001"):
        self.ip_addr = ip_addr
        self.port = port

    """
    Gets an overview of the loaded protocol models, called theories, of the
    interactive Tamarin server.

    Returns a JSON with the following schema:
    { 'theories': [ { 'theoryIndex': Int, 'theoryKind': ('trace' | 'diff'), 'theoryName': String } ] }

    Each entry in the JSON array corresponds to a protocol model. The 'theoryIndex'
    is used for index access to the model, the 'theoryKind' defines whether
    the model deals with trace or observational equivalence properties, and
    the 'theoryName' is the user-chosen name of the protocol model.
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
            , 'proofMethod': String
            , 'proofStatus': (IncompleteProof | CompleteProof
                             | TraceFound | InvalidatedProof
                             | UnfinishableProof | UndeterminedProof)
            , 'constraintSystem': String
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
    { 'proofMethods': [ {'proofMethod': String
                      , 'sourceRule': String} ] -- The available proof methods and their source rules
    , 'proofState': Proof                       -- The state of the proof
    }
    """

    def get_proof_state(self, theory_kind, theory_index, lemma, proof_path=[]):
        proof_path = "/".join(proof_path)
        # If path is NOT empty, we need to prepend a '/'
        if len(proof_path) > 0:
            proof_path = "/" + proof_path
        return requests.get(
            self.proof_state_route.format(
                self.ip_addr, self.port, theory_kind, theory_index, lemma, proof_path
            )
        )

    def apply_method_at_path(
        self, theory_kind, theory_index, lemma, proof_method_index, proof_path=[]
    ):
        # TODO: Figure out how Tamarin handles empty, non-empty proof paths for this route.
        return requests.get(
            self.main_method_route.format(
                self.ip_addr,
                self.port,
                theory_kind,
                theory_index,
                lemma,
                proof_path,
                proof_method_index,
            )
        )
