
from quantopian.pipeline import Pipeline
from quantopian.algorithm import attach_pipeline, pipeline_output
from quantopian.pipeline.filters.morningstar import Q1500US
from quantopian.pipeline.data.sentdex import sentiment
from quantopian.pipeline.data.morningstar import operation_ratios


def initialize(context):


# Rebalance every day, 1 hour after market open.
    schedule_function(my_rebalance, date_rules.every_day(), time_rules.market_open(hours=1))
 
# Record tracking variables at the end of each day.
    schedule_function(my_record_vars, date_rules.every_day(), time_rules.market_close())
 
# Create our dynamic stock selector.
    attach_pipeline(make_pipeline(), 'my_pipeline')
#set_commission(commission.PerTrade(cost=0.001))


def make_pipeline():

    testing_factor1 = operation_ratios.operation_margin.latest
    testing_factor2 = operation_ratios.revenue_growth.latest
    testing_factor3 = sentiment.sentiment_signal.latest

    universe = (Q1500US() &
         testing_factor1.notnull() &
         testing_factor2.notnull() &
         testing_factor3.notnull())

    testing_factor1 = testing_factor1.rank(mask=universe, method='average')
    testing_factor2 = testing_factor2.rank(mask=universe, method='average')
    testing_factor3 = testing_factor3.rank(mask=universe, method='average')

    testing_factor = testing_factor1 + testing_factor2 + testing_factor3

    testing_quantiles = testing_factor.quantiles(2)


    pipe = Pipeline(columns={
                        'testing_factor':testing_factor,
                        'shorts': testing_quantiles.eq(0),
                        'longs': testing_quantiles.eq(1)},
               screen= universe)
    return pipe


def before_trading_start(context, data):
    try:

#Called every day before market open.

        context.output = pipeline_output('my_pipeline')

# These are the securities that we are interested in             trading each day.
        context.security_list = context.output.index
    except Exception as e:
        print(str(e))


def my_rebalance(context,data):

#half shorts, half longs (near 0 beta)
#Execute orders according to our schedule_function() timing.

#compute the weighting of our portfolio
    long_secs= context.output[context.output['longs']].index
    long_weight = 0.5 / len(long_secs)
    short_secs= context.output[context.output['shorts']].index
    short_weight = -0.5 / len(short_secs)

    #open the long positions
    for security in long_secs:
        if data.can_trade(security):
            order_target_percent(security, long_weight)
            #open the short positions
    for security in short_secs:
        if data.can_trade(security):
            order_target_percent(security, short_weight)
    #close positions that are not in pipeline anymore
    for security in context.portfolio.positions:
        if data.can_trade(security) and security not in long_secs and security not in short_secs:
            order_target_percent(security,0)


def my_record_vars(context, data):

        #Plot variables at the end of each day.

    long_count =0
    short_count =0

    for position in context.portfolio.positions.itervalues():
        if position.amount>0:
            long_count+=1
        elif position.amount< 0:
            short_count +=1

        record(num_longs = long_count, num_shorts = short_count, leverage = context.account.leverage)