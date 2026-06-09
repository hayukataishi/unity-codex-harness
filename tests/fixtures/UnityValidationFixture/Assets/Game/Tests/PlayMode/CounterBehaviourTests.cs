using System.Collections;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
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

        [UnityTest]
        public IEnumerator Debug003Ac04_FixtureSceneLoadsConnectedPrefab()
        {
            yield return SceneManager.LoadSceneAsync(
                "FixtureScene",
                LoadSceneMode.Single);

            var root = GameObject.Find("CounterFixture");
            Assert.That(root, Is.Not.Null);

            var counter = root.GetComponent<CounterBehaviour>();
            Assert.That(counter, Is.Not.Null);
            Assert.That(counter.Target, Is.Not.Null);

            counter.Increment();
            yield return null;

            Assert.That(counter.Value, Is.EqualTo(1));
        }
    }
}
