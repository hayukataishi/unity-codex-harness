using System.Collections;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.TestTools;

namespace UnityCodexHarness.Fixture.Tests.PlayMode
{
    public sealed class CounterBehaviourTests
    {
        [UnityTest]
        public IEnumerator Increment_WhenCalledDuringPlayMode_IncreasesValue()
        {
            var gameObject = new GameObject("Counter");
            var counter = gameObject.AddComponent<CounterBehaviour>();

            counter.Increment();
            yield return null;

            Assert.That(counter.Value, Is.EqualTo(1));

            Object.Destroy(gameObject);
        }
    }
}
