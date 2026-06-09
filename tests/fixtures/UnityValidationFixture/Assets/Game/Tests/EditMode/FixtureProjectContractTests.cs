using System.Linq;
using NUnit.Framework;
using UnityCodexHarness.Fixture.Editor;
using UnityEditor;
using UnityEditor.Build.Profile;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace UnityCodexHarness.Fixture.Tests.EditMode
{
    public sealed class FixtureProjectContractTests
    {
        [Test]
        public void Debug003Ac02_SavedPrefabAndBuildProfileAreConnected()
        {
            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(
                FixtureProjectContract.PrefabPath);
            Assert.That(prefab, Is.Not.Null);

            var behaviour = prefab.GetComponent<CounterBehaviour>();
            Assert.That(behaviour, Is.Not.Null);
            Assert.That(behaviour.Target, Is.Not.Null);
            Assert.That(behaviour.Target.transform.IsChildOf(prefab.transform));

            var profile = AssetDatabase.LoadAssetAtPath<BuildProfile>(
                FixtureProjectContract.BuildProfilePath);
            Assert.That(profile, Is.Not.Null);
            Assert.That(profile.overrideGlobalScenes, Is.True);
            Assert.That(profile.scenes, Has.Length.EqualTo(1));
            Assert.That(
                profile.scenes[0].path,
                Is.EqualTo(FixtureProjectContract.ScenePath));
            Assert.That(profile.scenes[0].enabled, Is.True);
            Assert.That(
                profile.scriptingDefines,
                Does.Contain(FixtureProjectContract.ScriptingDefine));
        }

        [Test]
        public void Debug003Ac02_SavedSceneContainsPrefabInstance()
        {
            var previousSetup = EditorSceneManager.GetSceneManagerSetup();
            try
            {
                var scene = EditorSceneManager.OpenScene(
                    FixtureProjectContract.ScenePath,
                    OpenSceneMode.Single);
                var root = scene.GetRootGameObjects()
                    .Single(gameObject => gameObject.name == "CounterFixture");
                var behaviour = root.GetComponent<CounterBehaviour>();

                Assert.That(
                    PrefabUtility.GetPrefabAssetPathOfNearestInstanceRoot(root),
                    Is.EqualTo(FixtureProjectContract.PrefabPath));
                Assert.That(behaviour, Is.Not.Null);
                Assert.That(behaviour.Target, Is.Not.Null);
            }
            finally
            {
                if (previousSetup.Any(item => item.isLoaded))
                {
                    EditorSceneManager.RestoreSceneManagerSetup(previousSetup);
                }
                else
                {
                    EditorSceneManager.NewScene(
                        NewSceneSetup.EmptyScene,
                        NewSceneMode.Single);
                }
            }
        }
    }
}
