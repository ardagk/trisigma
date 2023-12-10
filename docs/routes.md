GetStrategyAllocationUseCase:
use portfolio repository to return a dict with allocation and namings

UpdateStrategyAllocationUseCase
skip this for now

GetStrategyDefinitionsUseCase
use trader repository to fetch strategy definitions and return as is

GetPortfolioPositionUseCase
find every account binded to this portfolio manager and fetch position of each of them, aggregate it and return

GetReturnComparisonUseCase
skip this for now

GetTransactionsUseCase
use order repository to search orders of the given instance_id whose order_status is FILLED, return orders as is

GetOpenOrdersUseCase
use order repository to search orders of the given instance_id whose order_status is SUBMITTED,  return orders as is

GetTraderJournalUseCase
use trader repository to fetch the journal (comments) of the instance_id and return it as is

GetObservationsUseCase
use trader repository to fetch the observations of the instance_id and return it as is

GetActiveBotsUseCase
use trader repository to find the active traders of the portfolio manager and return objects as dict
