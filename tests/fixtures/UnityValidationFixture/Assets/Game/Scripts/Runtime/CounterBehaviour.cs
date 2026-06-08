using UnityEngine;

namespace UnityCodexHarness.Fixture
{
    public sealed class CounterBehaviour : MonoBehaviour
    {
        [SerializeField]
        private GameObject target;

        private readonly Counter _counter = new Counter();

        public int Value => _counter.Value;
        public GameObject Target => target;

        public void Increment()
        {
            _counter.Increment();
        }

        public void SetTarget(GameObject value)
        {
            target = value;
        }
    }
}
