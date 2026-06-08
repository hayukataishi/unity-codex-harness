using UnityEngine;

namespace UnityCodexHarness.Fixture
{
    public sealed class CounterBehaviour : MonoBehaviour
    {
        private readonly Counter _counter = new Counter();

        public int Value => _counter.Value;

        public void Increment()
        {
            _counter.Increment();
        }
    }
}
