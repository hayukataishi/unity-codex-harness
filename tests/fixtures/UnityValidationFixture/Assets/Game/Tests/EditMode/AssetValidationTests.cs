using System.Linq;
using NUnit.Framework;
using UnityCodexHarness.Validation.Editor;
using UnityEditor;
using UnityEngine;

namespace UnityCodexHarness.Fixture.Tests.EditMode
{
    public sealed class AssetValidationTests
    {
        private const string TestFolder = "Assets/TempAssetValidationTests";
        private const string PrefabPath = TestFolder + "/ReferenceFixture.prefab";
        private const string TargetPrefabPath = TestFolder + "/Target.prefab";

        [TearDown]
        public void TearDown()
        {
            AssetDatabase.DeleteAsset(TestFolder);
        }

        [Test]
        public void Debug003Ac03_ProjectAssetsPassConfiguredValidation()
        {
            CreateReferencePrefab(useExternalTarget: false);

            var report = AssetValidator.ValidateProject(
                AssetValidator.DefaultConfigPath);

            Assert.That(
                report.errors,
                Is.Empty,
                string.Join(
                    "\n",
                    report.errors.Select(issue => $"{issue.code}: {issue.message}")));
            Assert.That(report.status, Is.EqualTo("PASS"));
            Assert.That(report.summary.requiredAssets, Is.EqualTo(4));
            Assert.That(report.summary.requiredReferences, Is.EqualTo(1));
            Assert.That(report.summary.scannedPrefabs, Is.GreaterThanOrEqualTo(1));
        }

        [Test]
        public void Debug003Ac03_DetectsBrokenSerializedObjectReference()
        {
            CreateReferencePrefab(useExternalTarget: true);
            AssetDatabase.DeleteAsset(TargetPrefabPath);
            AssetDatabase.Refresh();

            var report = AssetValidator.ValidateProject(
                AssetValidator.DefaultConfigPath);

            Assert.That(report.status, Is.EqualTo("FAIL"));
            Assert.That(
                report.errors.Any(
                    issue => issue.code == "MISSING_OBJECT_REFERENCE"),
                Is.True);
        }

        [Test]
        public void Debug003Ac03_DetectsMissingRequiredPrefabReference()
        {
            AssetDatabase.CreateFolder("Assets", "TempAssetValidationTests");
            var root = new GameObject("ReferenceFixture");
            root.AddComponent<CounterBehaviour>();
            PrefabUtility.SaveAsPrefabAsset(root, PrefabPath);
            Object.DestroyImmediate(root);

            var settings = new AssetValidationSettings
            {
                requiredReferences = new[]
                {
                    new RequiredReferenceRule
                    {
                        assetPath = PrefabPath,
                        objectPath = "ReferenceFixture",
                        componentType = typeof(CounterBehaviour).FullName,
                        propertyPath = "target",
                    },
                },
            };
            var report = new AssetValidationReport();

            AssetValidator.ValidateRequiredReferences(settings, report);
            report.Complete();

            Assert.That(report.status, Is.EqualTo("FAIL"));
            Assert.That(
                report.errors.Any(
                    issue => issue.code == "REQUIRED_REFERENCE_MISSING"),
                Is.True);
        }

        private static void CreateReferencePrefab(bool useExternalTarget)
        {
            AssetDatabase.CreateFolder("Assets", "TempAssetValidationTests");
            var root = new GameObject("ReferenceFixture");
            var behaviour = root.AddComponent<CounterBehaviour>();

            if (useExternalTarget)
            {
                var targetRoot = new GameObject("Target");
                PrefabUtility.SaveAsPrefabAsset(targetRoot, TargetPrefabPath);
                Object.DestroyImmediate(targetRoot);
                behaviour.SetTarget(
                    AssetDatabase.LoadAssetAtPath<GameObject>(TargetPrefabPath));
            }
            else
            {
                var child = new GameObject("Target");
                child.transform.SetParent(root.transform);
                behaviour.SetTarget(child);
            }

            PrefabUtility.SaveAsPrefabAsset(root, PrefabPath);
            Object.DestroyImmediate(root);
        }
    }
}
