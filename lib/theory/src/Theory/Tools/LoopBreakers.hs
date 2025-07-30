{-# LANGUAGE FlexibleContexts           #-}
{-# LANGUAGE GeneralizedNewtypeDeriving #-}
-- |
-- Copyright   : (c) 2012 Simon Meier
-- License     : GPL v3 (see LICENSE)
--
-- Portability : portable
--
-- Computate the loop-breakers in the premise-conclusion graph of a set of
-- multiset rewriting rules.
module Theory.Tools.LoopBreakers (

  -- * Computing loop breakers for solving premises
  useAutoLoopBreakersAC,
  ffgRelAc
  ) where

-- import Control.Applicative
import Control.Monad.Fresh
import Control.Monad.Reader

import Data.DAG.Simple

import Theory.Model


-- | An over-approximation of the dependency of solving premises. An element
-- @((fromRu, fromPrem), (toRu, toPrem))@ denotes that solving the premise
-- @(fromRu,fromPrem)@ might lead to a case where the premise @(toRu, toPrem)@
-- is open.
premSolvingRelAC :: (a -> [(PremIdx, LNFact)])  -- ^ Enumerate premises
                 -> (a -> [(ConcIdx, LNFact)])  -- ^ Enumerate conclusions
                 -> (a -> [LNSubstVFresh])      -- ^ Enumerate variants
                 -> [a]                         -- ^ Base carrier
                 -> WithMaude (Relation (a, PremIdx))
premSolvingRelAC ePrems eConcs eVariants rules = reader $ \hnd -> do
    (toRu, from) <- dataflowRelAC hnd
    (toPrem, _)  <- ePrems toRu
    return (from, (toRu, toPrem))
  where
    -- An over-approxmiation of the dataflow relation. An element @(fromRu,
    -- (toRu, toPrem))@ denotes that there is a conclusion of @fromRu@
    -- unifying with the premise @(toRu, toPrem)@.
    dataflowRelAC hnd = do
        ruFrom <- rules
        ruTo   <- rules
        (premIdx, premFa0) <- ePrems ruTo
        -- NoSource Facts are already explicitly excluded from precomputation
        guard $ not (isNoSourcesFact premFa0)
        guard $ or $ do
            premFa <- instances ruTo premFa0
            concFa <- instances ruFrom =<< (snd <$> eConcs ruFrom)
            let concFaFresh = rename concFa `evalFresh` avoid premFa
            return $ (`runReader` hnd) (unifiableLNFacts concFaFresh premFa)
        return (ruFrom, (ruTo, premIdx))

    instances ru fa = do
        subst <- eVariants ru
        return (apply (subst `freshToFreeAvoiding` fa) fa)
      
-- An over-approxmiation of the dataflow relation. An element @(fromRu,
-- toRu)@ denotes that there is a variant of a @fact@ conclusion of @fromRu@
-- unifying with a variant of a @fact@ premise of @toRu@.
ffgRelAc :: (a -> [(PremIdx, LNFact)])  -- ^ Enumerate premises
         -> (a -> [(ConcIdx, LNFact)])  -- ^ Enumerate conclusions
         -> (a -> [LNSubstVFresh])      -- ^ Enumerate variants
         -> [a]                         -- ^ Base carrier
         -> FactTag                     -- ^ Fact for which to compute the relation
         -> WithMaude (Relation a)
ffgRelAc ePrems eConcs eVariants rules fact = reader $ \hnd -> do
    (fromRu, toRu) <- dataflowRelAC hnd
    return (fromRu, toRu)
      where
        dataflowRelAC hnd = do
            ruFrom <- rules
            ruTo   <- rules
            -- For all premises
            (_, premFa0) <- ePrems ruTo
            -- Only for facts with the same tag as the given fact
            guard $ fact == factTag premFa0
            -- NoSource Facts are already explicitly excluded from precomputation
            guard $ not (isNoSourcesFact premFa0)
            -- For all conclusions
            (_, concFa0) <- eConcs ruFrom
            guard $ or $ do
                premFa <- instances ruTo premFa0
                concFa <- instances ruFrom concFa0
                let concFaFresh = rename concFa `evalFresh` avoid premFa
                return $ (`runReader` hnd) (unifiableLNFacts concFaFresh premFa)
            return (ruFrom, ruTo)

        instances ru fa = do
            subst <- eVariants ru
            return (apply (subst `freshToFreeAvoiding` fa) fa)


-- | Replace all loop-breaker information with loop-breakers computed
-- automatically from the dataflow relation 'dataflowRelAC'.
useAutoLoopBreakersAC
  :: Ord a
  => (a -> [(PremIdx, LNFact)])  -- ^ Enumerate premises
  -> (a -> [(ConcIdx, LNFact)])  -- ^ Enumerate conclusions
  -> (a -> [LNSubstVFresh])      -- ^ Enumerate variants
  -> ([PremIdx] -> a -> a)       -- ^ Add annotation
  -> [a]                         -- ^ Original rules
  -> WithMaude ([a], Relation (a, PremIdx), [(a, PremIdx)])
  -- ^ Annotated rules and the premise solving relation
useAutoLoopBreakersAC ePrems eConcs eVariants addAnn rules =
    reader $ \hnd ->
      let solveRel = (`runReader` hnd) $
              premSolvingRelAC ePrems eConcs eVariants rules
          breakers = dfsLoopBreakers $ solveRel
      in ( do ru <- rules
              return (addAnn [ u | (ru', u) <- breakers, ru == ru' ] ru)
         , solveRel
         , breakers
         )

