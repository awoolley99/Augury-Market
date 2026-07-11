# ADR 0006: SnapTrade for brokerage account linking (Robinhood, etc.)

## Status
Accepted

## Context
Users want to link a real brokerage account (Robinhood specifically was
requested) so their actual holdings show up alongside Augury Market's
research. Robinhood has no public developer API -- there is no way for any
third-party application to connect directly to a Robinhood account. The
only legitimate path is through a licensed aggregator whose hosted flow
handles the user's real brokerage login.

## Decision
Use SnapTrade, behind a provider-agnostic `BrokerageProvider` interface
(same modular pattern as market data, ADR 0005), with a deterministic
`stub` provider as the default so the feature is fully buildable, testable,
and demoable without a real SnapTrade account or any real financial data.

## Rationale
- SnapTrade is purpose-built for brokerage/investment account linking
  (versus Plaid, which is a much broader company covering banking,
  identity, income, etc., with investments as one product among many) and
  has a straightforward, well-documented read-only holdings API.
- SnapTrade publishes an official Python SDK (`snaptrade-python-sdk`) with
  native async methods, which we use directly rather than hand-rolling
  their HMAC request-signing scheme ourselves -- meaningfully lower risk of
  a subtly broken auth implementation.
- The user's actual brokerage password is entered on SnapTrade's hosted
  Connection Portal, never on our servers. We only ever store a scoped,
  revocable `userSecret` -- functionally a per-user API key, not a
  credential -- which is encrypted at rest (see below) and can be revoked
  by disconnecting.

## Consequences
- **Cost and setup**: SnapTrade requires signing up as a business and
  accepting their terms; production usage is not necessarily free. Setting
  up the actual developer account, obtaining `SNAPTRADE_CLIENT_ID` /
  `SNAPTRADE_CONSUMER_KEY`, and any compliance considerations that come
  with handling real financial data are on the app owner, not something
  automatable from a coding session.
- **Separate encryption key**: `BROKERAGE_TOKEN_ENCRYPTION_KEY` (Fernet,
  `app/core/crypto.py`) is deliberately independent from `SECRET_KEY` (JWT
  signing) -- rotating one should never force rotating the other, and a
  leak of one shouldn't automatically compromise the other.
- **Unverified response parsing**: the exact nested field names SnapTrade
  returns for holdings/positions (`SnapTradeBrokerageProvider._extract_*`
  logic) were implemented from publicly documented shapes and the SDK's
  confirmed method signatures, but without network access to a real
  SnapTrade sandbox account to verify the exact JSON field names end to
  end. This should be smoke-tested against a real connected account before
  being trusted, and field lookups adjusted if anything comes back
  differently than expected. Every other provider integration in this
  codebase (market data stub, Anthropic AI summaries) was verified against
  either a real API or a fully mocked test suite matching documented
  shapes; this one carries a bit more first-real-use risk as a result.
- **One brokerage identity per app user, for now**: `BrokerageConnection`
  is one-to-one with a user, though SnapTrade itself supports multiple
  brokerage connections under a single SnapTrade user. Multiple *brokerages*
  per app user (e.g. Robinhood + Schwab) would already work today since
  that's a SnapTrade-side concept; multiple *SnapTrade users* per app user
  isn't supported and isn't an obviously useful thing to add.
