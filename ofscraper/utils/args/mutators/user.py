from copy import deepcopy
import ofscraper.utils.args.accessors.read as read_args


def resetUserFilters():
    args = deepcopy(read_args.retriveArgs())
    args.userlist = []
    args.blacklist = []
    args.renewal = None
    args.sub_status = None
    args.last_seen = None
    args.last_seen_after = None
    args.last_seen_before = None
    args.promo = None
    args.all_promo = None
    args.free_trial = None
    args.regular_price = None
    args.renewal_price = None
    args.current_price = None
    args.promo_price = None
    args.promo_price_min = None
    args.promo_price_max = None
    args.regular_price_min = None
    args.regular_price_max = None
    args.current_price_min = None
    args.current_price_max = None
    args.renewal_price_min = None
    args.renewal_price_max = None
    args.expired_before = None
    args.expired_after = None
    args.subscribed_before = None
    args.subscribed_after = None
    args.sort = "name"
    args.desc = False
    return args


def resetUserSelect():
    args = deepcopy(read_args.retriveArgs())
    args.usernames = None
    return args
