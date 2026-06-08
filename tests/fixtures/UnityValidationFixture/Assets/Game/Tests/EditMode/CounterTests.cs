using NUnit.Framework;

namespace UnityCodexHarness.Fixture.Tests.EditMode
{
    public sealed class CounterTests
    {
        [Test]
        public void Increment_WhenCalled_IncreasesValue()
        {
            var counter = new Counter();

            counter.Increment();

            Assert.That(counter.Value, Is.EqualTo(1));
        }
    }
}
