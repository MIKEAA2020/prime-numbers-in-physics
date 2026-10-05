# Pre-registered protocol: Chebotarev dictionary fit to an exhaustive branching table

**Status of this document.** This is the frozen analysis protocol for the
$\mathsf{C9}$ dictionary application to measured branching fractions. It is
committed to the repository before the fit below is executed; the commit hash
and timestamp constitute the freeze. Earlier compatibility checks on the
same $Z$-pole table used an unconstrained variant of the fit and are not part
of the confirmatory protocol; they are reported only as sensitivity.

## 1. Hypothesis under test

$H_1$ (dictionary signature): there exists an exhaustive set of $k$ measured
decay channels of a single particle whose branching fractions satisfy
$f_i = c_i/N + \epsilon_i$ with a common integer $N$, integers $c_i \ge 1$
with $c_i \mid N$ and $\sum_i c_i = N$ (the class equation), and
$\epsilon_i$ at most the quoted measurement uncertainty. The integers
$(N, \{c_i\})$ are interpreted as a conjugacy-class-size vector of a group of
order $N$ (each $|C| \mid |G|$ by orbit–stabilizer); the fit space is the
arithmetic superset of realizable class vectors, which is conservative
(it can only inflate the false-positive rate).

$H_0$ (structureless null): the table is a draw from the uniform
distribution on the $(k-1)$-simplex (Dirichlet$(1,\dots,1)$), measured with
the same uncertainty pattern.

## 2. Data, fixed before the fit

* **Primary ensemble (confirmatory).** The exhaustive $Z$-boson 5-channel
  branching table, PDG values: channels
  $\{\mathrm{had}, e, \mu, \tau, \mathrm{invisible}\}$ with
  $f = (0.6991,\; 0.03363,\; 0.03366,\; 0.03370,\; 0.2017)$ and
  $\sigma = (0.0009,\; 0.00004,\; 0.00007,\; 0.00009,\; 0.0006)$.
  The channels are exhaustive, so the model's $\sum_i f_i = 1$ is tested
  channel-by-channel without preprocessing; no renormalization is applied.
* **Excluded by the registered admission rule** ($k \ge 5$ channels
  and $\sigma_i \le 0.003$ absolute in every channel): $W$ ($k=4$),
  $\tau$ ($k=3$), $\mu$ ($k=1$). Higgs decays have $\sigma_i$ above the
  registered precision at present. A finer $Z$-pole granularity
  (splitting hadrons into $c\bar c$, $b\bar b$, light) requires a frozen
  PDG extract and is deferred to the first protocol update, not fitted here.

## 3. Test statistic

$$
T(\{f_i,\sigma_i\}) \;=\; \min_{\substack{N \in [5,\,360]\\ c_i \mid N,\;
\sum_i c_i = N}} \;\sum_{i=1}^{k} \frac{(f_i - c_i/N)^2}{\sigma_i^2}.
$$

The minimization is exact (dynamic program over integer partial sums; the
class-equation constraint $\sum c_i = N$ is enforced at the final stage).
The group-order range $N \le 360$ is the registered dictionary range. The
registered sensitivity variants (reported, non-confirmatory): the
unconstrained fit ($\sum_i c_i = N$ dropped, $N \le 5000$) used in the
earlier compatibility check.

## 4. Null distribution and decision rule

Monte Carlo, $M = 5000$ trials: tables drawn Dirichlet$(1,\dots,1)$, $k=5$,
each fitted with the same constrained statistic and the **actual uncertainty
pattern** of the primary ensemble. The false-positive rate at the registered
threshold $\chi^2_{0.95}(k-1)$ and the empirical null distribution of $T$
are calibrated from these trials.

Decision rule (frozen):
* *signature present* iff the observed $T_{\mathrm{obs}}$ satisfies
  $p_{\mathrm{pres}} = \mathrm{Prob}(T_{\mathrm{null}} \le T_{\mathrm{obs}}) \ge 0.05$;
* otherwise *signature absent* at the primary ensemble, reported together
  with (i) the power of the test at the actual precision, and (ii) the
  precision inflation factor $\lambda = \sqrt{T_{\mathrm{obs}}/\chi^2_{0.95}}$,
  the factor by which all uncertainties would have to grow for the best
  constrained fit to become acceptable.

## 5. Power (registered truth tables)

Injected truth tables, $k=5$, one per decade of the group-order range, each
with the $Z$-table's sparsity profile (one dominant channel):

| $N$ | $\{c_i\}$ |
|-----|------------|
| 6   | $(2, 1, 1, 1, 1)$ |
| 36  | $(18, 6, 6, 4, 2)$ |
| 360 | $(180, 90, 45, 36, 9)$ |

For each truth table, 2000 noise realizations at the actual uncertainty
pattern: power $= $ fraction with $T \le \chi^2_{0.95}(k-1)$ and correct
recovery $N$. The same computation is repeated with all uncertainties
scaled by $10^{-1}$, $10^{-2}$, and $3\times10^{-3}$ (the statistical-floor
scenario for a $Z$ factory with $\sim 10^{12}$ recorded $Z$ decays versus
$\sim 2\times10^{7}$ at LEP, for which the relative improvement is
$\sqrt{2\times10^{7}/1.8\times10^{12}} \approx 3.3\times10^{-3}$).

## 6. Reporting

Reported outputs: $T_{\mathrm{obs}}$, best-fit $(N, \{c_i\})$,
$p_{\mathrm{pres}}$, the empirical null median and 95th percentile, power at
each truth table and uncertainty scenario, the precision inflation factor,
and the minimum group order excluded by each channel individually. The
absence verdict is joint with the power statement: absence with power
$\approx 1$ over the whole registered range is an exclusion at the
$Z$ scale; absence with power $< 0.5$ carries no information.

## 7. Interpretation policy

The $\mathsf{C9}$ dictionary places the signature at the unification scale,
not the electroweak scale. A powered exclusion at the $Z$ pole is consistent
with that placement and carries no confirmatory content for $\mathsf{C9}$;
it bounds the dictionary's reach downward and fixes what future precision
tables must achieve for a decisive test.
