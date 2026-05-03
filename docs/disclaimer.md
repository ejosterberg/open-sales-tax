# Disclaimer

OpenSalesTax is a **calculation engine** for US sales tax. It is
**not** legal advice, tax advice, or a tax-filing service.

Per [constitution §13](../specs/constitution.md), every API
response that returns a tax calculation includes a `disclaimer`
field reiterating this point.

## What OpenSalesTax does

- Parses publicly-available rate and boundary data
- Calculates how much sales tax a given transaction *should*
  produce, based on the loaded data and your supplied taxability
  category
- Returns the per-jurisdiction breakdown so you can see where
  every basis point comes from

## What OpenSalesTax does NOT do

- File returns with state Departments of Revenue
- Tell you whether you have nexus in a state (i.e. whether you're
  obligated to collect tax there)
- Provide tax planning advice
- Substitute for a CPA, tax attorney, or compliance professional

## Verify before remitting

Before remitting tax to any jurisdiction:

1. **Cross-check your rate** against your state Department of
   Revenue's official lookup tool. Most states publish one online.
2. **Confirm your taxability category** is correct for your
   product. The matrices shipped in OpenSalesTax cover common
   cases; novel products may need state-specific rulings.
3. **Confirm you have nexus** in the jurisdiction you're
   collecting for. Post-Wayfair (2018) economic nexus rules vary
   by state.
4. **For complex situations** (multi-state operations, marketplace
   facilitator obligations, exemption certificates), consult a
   tax professional.

## Per-state Department of Revenue lookup tools

| State | Lookup URL |
|---|---|
| MN | https://www.revenue.state.mn.us/sales-tax-rate-calculator |
| WI | https://www.revenue.wi.gov/Pages/FAQS/pcs-rates.aspx |
| CA | https://www.cdtfa.ca.gov/services/#Look-Up-Sales-Use-Tax-Rates |
| TX | https://comptroller.texas.gov/taxes/sales/city.php |
| NY | https://www.tax.ny.gov/bus/st/sales-tax-rates.htm |
| FL | https://floridarevenue.com/taxes/taxesfees/Pages/discretionary.aspx |
| (other states) | search "<state name> department of revenue sales tax rate lookup" |

## Limitation of liability

OpenSalesTax is provided **AS IS** under the [Apache License 2.0](
../LICENSE), without warranty of any kind. The maintainers and
contributors are not liable for any tax penalty, audit finding,
or business loss resulting from the use of this software. See
the LICENSE file for the full warranty disclaimer (sections 7
and 8).

## Reporting incorrect calculations

If you believe OpenSalesTax produces an incorrect result for a
specific transaction:

1. Verify against your state DOR's official lookup tool.
2. If it disagrees, please open a GitHub issue with:
   - The exact API request that produced the wrong result
   - The expected rate and your source for it
   - The relevant state and ZIP

The state's maintainer (or, if vacant, the project maintainer)
will investigate and patch the state module if needed.
