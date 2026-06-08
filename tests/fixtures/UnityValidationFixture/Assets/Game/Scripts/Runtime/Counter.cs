namespace UnityCodexHarness.Fixture
{
    public sealed class Counter
    {
        public int Value { get; private set; }

        public void Increment()
        {
            Value++;
        }
    }
}
