export function useSubscription(backend, user) {
  const limit = backend?.free_daily_limit ?? null;
  const subscriptionEnabled = backend?.subscription_enabled ?? false;

  const plan = user?.plan ?? "free";
  const usageToday = user?.usage_today ?? 0;

  const isPro = plan === "pro";
  const overLimit = !isPro && limit != null && usageToday >= limit;

  return {
    subscriptionEnabled,
    plan,
    isPro,
    usageToday,
    limit,
    overLimit,
    user,
  };
}


