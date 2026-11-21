# Published-figure reproduction guidance

- [PAPER-TARGET-01] Target Saratz et al., *Nature Communications* 7, 13611 (2016), Figure 9(a-b), DOI `10.1038/ncomms13611`.
- [PAPER-PARAM-02] Preserve the reported physical target: unfrustrated square-lattice 2D Ising model, zero field, `J = k_B = 1`, and `L = 10, 20, 40` over `T/J = 1.5...3.0`. Keep periodic boundaries and `m_L = <|M|>/N` visibly labeled as this project's implementation choices.
- [PAPER-DISCLOSURE-03] Label this as an independent method reproduction. Never imply that unpublished random seeds, sweep counts, or original numerical data were recovered.
- [PAPER-SAMPLING-04] Record every tutorial-only sampling choice, seed, chain count, equilibration budget, measurement budget, and sample interval in machine-readable output.
- [PAPER-STATISTICS-05] Compute nonlinear observables within each independent chain before averaging; label uncertainty as SEM across chains, not autocorrelation-corrected uncertainty.
- [PAPER-FIGURE-06] Recreate the scientific relationship with newly simulated data. Do not copy pixels from the published figure. Export both 300 dpi PNG and vector PDF.

Exact Onsager values, measured Monte Carlo values, paper-reported parameters, and tutorial-selected parameters must remain visibly distinct.
