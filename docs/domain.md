``` mermaid

classDiagram

    class Order{
      +str order_ref
      +int account_id
      +time: float
      +Instrument instrument
      +str side
      +float qty
      +str status
      +str order_type
      +float price
      +str: tif
    }
    
    class Trader{
      +int trader_id
      +int account_id
      +str strategy_uri
      +float start_time
      +dict meta
    }

    class FinancialAccount{
      +int account_id
      +int portfolio_manager_id
      +str name
      +str platform
      +bool paper
      +dict meta
    }

    class PortfolioManager{
        +int portfolio_manager_id
        +str name
        +dict meta
    }

```
