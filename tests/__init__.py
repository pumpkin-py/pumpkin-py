# Since we want to import modules, we have to instantiate logger objects.
# We can use dummy 'object()' instead of the 'commands.Bot', as long as
# it is not 'None'.
import pie.logger

pie.logger.Bot.logger(object())
pie.logger.Guild.logger(object())
