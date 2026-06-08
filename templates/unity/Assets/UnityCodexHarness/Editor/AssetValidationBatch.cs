using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace UnityCodexHarness.Validation.Editor
{
    [Serializable]
    public sealed class RequiredAssetRule
    {
        public string path = string.Empty;
        public string type = string.Empty;
    }

    [Serializable]
    public sealed class RequiredReferenceRule
    {
        public string assetPath = string.Empty;
        public string objectPath = string.Empty;
        public string componentType = string.Empty;
        public string propertyPath = string.Empty;
    }

    [Serializable]
    public sealed class AssetValidationSettings
    {
        public RequiredAssetRule[] requiredAssets = Array.Empty<RequiredAssetRule>();
        public RequiredReferenceRule[] requiredReferences =
            Array.Empty<RequiredReferenceRule>();
    }

    [Serializable]
    public sealed class AssetValidationIssue
    {
        public string code = string.Empty;
        public string assetPath = string.Empty;
        public string objectPath = string.Empty;
        public string componentType = string.Empty;
        public string propertyPath = string.Empty;
        public string message = string.Empty;
    }

    [Serializable]
    public sealed class AssetValidationSummary
    {
        public int scannedScenes;
        public int scannedPrefabs;
        public int scannedScriptableObjects;
        public int requiredAssets;
        public int requiredReferences;
        public int errors;
        public int warnings;
    }

    [Serializable]
    public sealed class AssetValidationReport
    {
        public string status = "NOT RUN";
        public string unityVersion = string.Empty;
        public string configPath = string.Empty;
        public AssetValidationSummary summary = new AssetValidationSummary();
        public List<AssetValidationIssue> errors = new List<AssetValidationIssue>();
        public List<AssetValidationIssue> warnings = new List<AssetValidationIssue>();

        public void AddError(
            string code,
            string assetPath,
            string message,
            string objectPath = "",
            string componentType = "",
            string propertyPath = "")
        {
            errors.Add(
                new AssetValidationIssue
                {
                    code = code,
                    assetPath = assetPath,
                    objectPath = objectPath,
                    componentType = componentType,
                    propertyPath = propertyPath,
                    message = message,
                });
        }

        public void Complete()
        {
            summary.errors = errors.Count;
            summary.warnings = warnings.Count;
            status = errors.Count == 0 ? "PASS" : "FAIL";
        }
    }

    public static class AssetValidator
    {
        public const string DefaultConfigPath =
            "ProjectSettings/UnityCodexHarnessAssetValidation.json";

        private static readonly PropertyInfo ObjectReferenceEntityIdProperty =
            typeof(SerializedProperty).GetProperty(
                "objectReferenceEntityIdValue");

        public static AssetValidationReport ValidateProject(string configPath)
        {
            var report = new AssetValidationReport
            {
                unityVersion = Application.unityVersion,
                configPath = configPath,
            };
            var settings = LoadSettings(configPath, report);

            ScanPrefabs(report);
            ScanScenes(report);
            ScanScriptableObjects(report);
            ValidateRequiredAssets(settings, report);
            ValidateRequiredReferences(settings, report);
            report.Complete();
            return report;
        }

        public static void ValidateRequiredAssets(
            AssetValidationSettings settings,
            AssetValidationReport report)
        {
            var rules = settings.requiredAssets ?? Array.Empty<RequiredAssetRule>();
            report.summary.requiredAssets = rules.Length;
            foreach (var rule in rules)
            {
                if (rule == null || string.IsNullOrWhiteSpace(rule.path))
                {
                    report.AddError(
                        "INVALID_REQUIRED_ASSET_RULE",
                        string.Empty,
                        "Required asset rule must contain a project-relative path.");
                    continue;
                }

                var asset = AssetDatabase.LoadMainAssetAtPath(rule.path);
                if (asset == null)
                {
                    report.AddError(
                        "REQUIRED_ASSET_MISSING",
                        rule.path,
                        "Required asset could not be loaded.");
                    continue;
                }

                if (!string.IsNullOrWhiteSpace(rule.type)
                    && !MatchesType(asset.GetType(), rule.type))
                {
                    report.AddError(
                        "REQUIRED_ASSET_TYPE_MISMATCH",
                        rule.path,
                        $"Expected {rule.type}, found {asset.GetType().FullName}.");
                }
            }
        }

        public static void ValidateRequiredReferences(
            AssetValidationSettings settings,
            AssetValidationReport report)
        {
            var rules =
                settings.requiredReferences ?? Array.Empty<RequiredReferenceRule>();
            report.summary.requiredReferences = rules.Length;
            foreach (var rule in rules)
            {
                ValidateRequiredReference(rule, report);
            }
        }

        private static AssetValidationSettings LoadSettings(
            string configPath,
            AssetValidationReport report)
        {
            var fullPath = ProjectPath(configPath);
            if (!File.Exists(fullPath))
            {
                report.AddError(
                    "VALIDATION_CONFIG_MISSING",
                    configPath,
                    "Asset validation configuration file does not exist.");
                return new AssetValidationSettings();
            }

            try
            {
                var settings =
                    JsonUtility.FromJson<AssetValidationSettings>(
                        File.ReadAllText(fullPath));
                if (settings == null)
                {
                    throw new InvalidDataException("Configuration deserialized to null.");
                }

                return settings;
            }
            catch (Exception exception)
            {
                report.AddError(
                    "VALIDATION_CONFIG_INVALID",
                    configPath,
                    exception.Message);
                return new AssetValidationSettings();
            }
        }

        private static void ScanPrefabs(AssetValidationReport report)
        {
            foreach (var path in FindAssetPaths("t:Prefab"))
            {
                var prefabAsset = AssetDatabase.LoadAssetAtPath<GameObject>(path);
                if (prefabAsset != null
                    && PrefabUtility.GetPrefabAssetType(prefabAsset)
                    == PrefabAssetType.Model)
                {
                    continue;
                }

                GameObject root = null;
                try
                {
                    root = PrefabUtility.LoadPrefabContents(path);
                    report.summary.scannedPrefabs++;
                    InspectHierarchy(root, path, report);
                }
                catch (Exception exception)
                {
                    report.AddError(
                        "PREFAB_INSPECTION_FAILED",
                        path,
                        exception.Message);
                }
                finally
                {
                    if (root != null)
                    {
                        PrefabUtility.UnloadPrefabContents(root);
                    }
                }
            }
        }

        private static void ScanScenes(AssetValidationReport report)
        {
            var setup = EditorSceneManager.GetSceneManagerSetup();
            var openedScene = false;
            try
            {
                foreach (var path in FindAssetPaths("t:Scene"))
                {
                    try
                    {
                        var scene =
                            EditorSceneManager.OpenScene(path, OpenSceneMode.Single);
                        openedScene = true;
                        report.summary.scannedScenes++;
                        foreach (var root in scene.GetRootGameObjects())
                        {
                            InspectHierarchy(root, path, report);
                        }
                    }
                    catch (Exception exception)
                    {
                        report.AddError(
                            "SCENE_INSPECTION_FAILED",
                            path,
                            exception.Message);
                    }
                }
            }
            finally
            {
                RestoreSceneSetup(setup, openedScene);
            }
        }

        private static void ScanScriptableObjects(AssetValidationReport report)
        {
            foreach (var path in FindAssetPaths("t:ScriptableObject"))
            {
                foreach (var asset in AssetDatabase.LoadAllAssetsAtPath(path))
                {
                    if (!(asset is ScriptableObject scriptableObject))
                    {
                        continue;
                    }

                    report.summary.scannedScriptableObjects++;
                    InspectSerializedObject(
                        scriptableObject,
                        path,
                        scriptableObject.name,
                        report);
                }
            }
        }

        private static IEnumerable<string> FindAssetPaths(string filter)
        {
            return AssetDatabase.FindAssets(filter, new[] { "Assets" })
                .Select(AssetDatabase.GUIDToAssetPath)
                .Where(path => !string.IsNullOrEmpty(path))
                .Distinct()
                .OrderBy(path => path, StringComparer.Ordinal);
        }

        private static void InspectHierarchy(
            GameObject root,
            string assetPath,
            AssetValidationReport report)
        {
            foreach (var transform in root.GetComponentsInChildren<Transform>(true))
            {
                var gameObject = transform.gameObject;
                var objectPath = HierarchyPath(root.transform, transform);
                var missingScripts =
                    GameObjectUtility.GetMonoBehavioursWithMissingScriptCount(gameObject);
                if (missingScripts > 0)
                {
                    report.AddError(
                        "MISSING_SCRIPT",
                        assetPath,
                        $"{missingScripts} missing script component(s).",
                        objectPath);
                }

                foreach (var component in gameObject.GetComponents<Component>())
                {
                    if (component == null)
                    {
                        continue;
                    }

                    InspectSerializedObject(
                        component,
                        assetPath,
                        objectPath,
                        report);
                }
            }
        }

        private static void InspectSerializedObject(
            UnityEngine.Object target,
            string assetPath,
            string objectPath,
            AssetValidationReport report)
        {
            try
            {
                var serializedObject = new SerializedObject(target);
                var property = serializedObject.GetIterator();
                while (property.Next(true))
                {
                    if (property.propertyType != SerializedPropertyType.ObjectReference)
                    {
                        continue;
                    }

                    if (property.objectReferenceValue == null
                        && HasUnresolvedReferenceId(property))
                    {
                        report.AddError(
                            "MISSING_OBJECT_REFERENCE",
                            assetPath,
                            "Serialized object reference cannot be resolved.",
                            objectPath,
                            target.GetType().FullName,
                            property.propertyPath);
                    }
                }
            }
            catch (Exception exception)
            {
                report.AddError(
                    "SERIALIZED_OBJECT_INSPECTION_FAILED",
                    assetPath,
                    exception.Message,
                    objectPath,
                    target.GetType().FullName);
            }
        }

        private static void ValidateRequiredReference(
            RequiredReferenceRule rule,
            AssetValidationReport report)
        {
            if (rule == null
                || string.IsNullOrWhiteSpace(rule.assetPath)
                || string.IsNullOrWhiteSpace(rule.propertyPath))
            {
                report.AddError(
                    "INVALID_REQUIRED_REFERENCE_RULE",
                    rule?.assetPath ?? string.Empty,
                    "Required reference rule needs assetPath and propertyPath.");
                return;
            }

            var extension = Path.GetExtension(rule.assetPath).ToLowerInvariant();
            if (extension == ".prefab")
            {
                ValidatePrefabReference(rule, report);
            }
            else if (extension == ".unity")
            {
                ValidateSceneReference(rule, report);
            }
            else
            {
                ValidateAssetReference(rule, report);
            }
        }

        private static void ValidatePrefabReference(
            RequiredReferenceRule rule,
            AssetValidationReport report)
        {
            GameObject root = null;
            try
            {
                root = PrefabUtility.LoadPrefabContents(rule.assetPath);
                var gameObject = FindInPrefab(root, rule.objectPath);
                ValidateComponentProperty(gameObject, rule, report);
            }
            catch (Exception exception)
            {
                report.AddError(
                    "REQUIRED_REFERENCE_INSPECTION_FAILED",
                    rule.assetPath,
                    exception.Message,
                    rule.objectPath,
                    rule.componentType,
                    rule.propertyPath);
            }
            finally
            {
                if (root != null)
                {
                    PrefabUtility.UnloadPrefabContents(root);
                }
            }
        }

        private static void ValidateSceneReference(
            RequiredReferenceRule rule,
            AssetValidationReport report)
        {
            var setup = EditorSceneManager.GetSceneManagerSetup();
            try
            {
                var scene =
                    EditorSceneManager.OpenScene(rule.assetPath, OpenSceneMode.Single);
                var gameObject = FindInScene(scene, rule.objectPath);
                ValidateComponentProperty(gameObject, rule, report);
            }
            catch (Exception exception)
            {
                report.AddError(
                    "REQUIRED_REFERENCE_INSPECTION_FAILED",
                    rule.assetPath,
                    exception.Message,
                    rule.objectPath,
                    rule.componentType,
                    rule.propertyPath);
            }
            finally
            {
                RestoreSceneSetup(setup, true);
            }
        }

        private static void ValidateAssetReference(
            RequiredReferenceRule rule,
            AssetValidationReport report)
        {
            var assets = AssetDatabase.LoadAllAssetsAtPath(rule.assetPath);
            var target = assets.FirstOrDefault(
                asset => asset != null
                    && (string.IsNullOrWhiteSpace(rule.componentType)
                        || MatchesType(asset.GetType(), rule.componentType)));
            if (target == null)
            {
                report.AddError(
                    "REQUIRED_REFERENCE_TARGET_MISSING",
                    rule.assetPath,
                    "Configured asset or target type could not be loaded.",
                    rule.objectPath,
                    rule.componentType,
                    rule.propertyPath);
                return;
            }

            ValidateProperty(target, rule, report);
        }

        private static void ValidateComponentProperty(
            GameObject gameObject,
            RequiredReferenceRule rule,
            AssetValidationReport report)
        {
            if (gameObject == null)
            {
                report.AddError(
                    "REQUIRED_GAME_OBJECT_MISSING",
                    rule.assetPath,
                    "Configured GameObject path was not found.",
                    rule.objectPath,
                    rule.componentType,
                    rule.propertyPath);
                return;
            }

            var component = gameObject.GetComponents<Component>()
                .FirstOrDefault(
                    candidate => candidate != null
                        && MatchesType(candidate.GetType(), rule.componentType));
            if (component == null)
            {
                report.AddError(
                    "REQUIRED_COMPONENT_MISSING",
                    rule.assetPath,
                    "Configured component type was not found.",
                    rule.objectPath,
                    rule.componentType,
                    rule.propertyPath);
                return;
            }

            ValidateProperty(component, rule, report);
        }

        private static void ValidateProperty(
            UnityEngine.Object target,
            RequiredReferenceRule rule,
            AssetValidationReport report)
        {
            var serializedObject = new SerializedObject(target);
            var property = serializedObject.FindProperty(rule.propertyPath);
            if (property == null)
            {
                report.AddError(
                    "REQUIRED_PROPERTY_MISSING",
                    rule.assetPath,
                    "Configured serialized property was not found.",
                    rule.objectPath,
                    rule.componentType,
                    rule.propertyPath);
                return;
            }

            var missing = false;
            if (property.propertyType == SerializedPropertyType.ObjectReference)
            {
                missing = property.objectReferenceValue == null;
            }
            else if (property.propertyType == SerializedPropertyType.ExposedReference)
            {
                missing = property.exposedReferenceValue == null;
            }
            else
            {
                report.AddError(
                    "REQUIRED_PROPERTY_NOT_REFERENCE",
                    rule.assetPath,
                    "Configured property is not an object reference.",
                    rule.objectPath,
                    rule.componentType,
                    rule.propertyPath);
                return;
            }

            if (missing)
            {
                report.AddError(
                    "REQUIRED_REFERENCE_MISSING",
                    rule.assetPath,
                    "Required serialized reference is null or unresolved.",
                    rule.objectPath,
                    rule.componentType,
                    rule.propertyPath);
            }
        }

        private static GameObject FindInPrefab(GameObject root, string objectPath)
        {
            if (root == null)
            {
                return null;
            }

            if (string.IsNullOrWhiteSpace(objectPath)
                || objectPath == root.name)
            {
                return root;
            }

            var relativePath = objectPath.StartsWith(
                root.name + "/",
                StringComparison.Ordinal)
                ? objectPath.Substring(root.name.Length + 1)
                : objectPath;
            var child = root.transform.Find(relativePath);
            return child != null ? child.gameObject : null;
        }

        private static GameObject FindInScene(Scene scene, string objectPath)
        {
            if (string.IsNullOrWhiteSpace(objectPath))
            {
                return null;
            }

            var segments = objectPath.Split('/');
            var root = scene.GetRootGameObjects()
                .FirstOrDefault(candidate => candidate.name == segments[0]);
            if (root == null || segments.Length == 1)
            {
                return root;
            }

            var child = root.transform.Find(string.Join("/", segments.Skip(1)));
            return child != null ? child.gameObject : null;
        }

        private static string HierarchyPath(Transform root, Transform target)
        {
            var names = new Stack<string>();
            var current = target;
            while (current != null)
            {
                names.Push(current.name);
                if (current == root)
                {
                    break;
                }

                current = current.parent;
            }

            return string.Join("/", names);
        }

        private static bool MatchesType(Type actual, string expected)
        {
            return string.IsNullOrWhiteSpace(expected)
                || actual.Name == expected
                || actual.FullName == expected;
        }

        private static bool HasUnresolvedReferenceId(SerializedProperty property)
        {
            if (ObjectReferenceEntityIdProperty != null)
            {
                var value = ObjectReferenceEntityIdProperty.GetValue(property);
                if (value == null)
                {
                    return false;
                }

                var defaultValue = Activator.CreateInstance(value.GetType());
                return !value.Equals(defaultValue);
            }

#pragma warning disable CS0618
            return property.objectReferenceInstanceIDValue != 0;
#pragma warning restore CS0618
        }

        private static void RestoreSceneSetup(
            SceneSetup[] setup,
            bool openedScene)
        {
            if (!openedScene)
            {
                return;
            }

            if (setup.Any(item => item.isLoaded))
            {
                EditorSceneManager.RestoreSceneManagerSetup(setup);
                return;
            }

            EditorSceneManager.NewScene(
                NewSceneSetup.EmptyScene,
                NewSceneMode.Single);
        }

        private static string ProjectPath(string relativePath)
        {
            var projectRoot = Directory.GetParent(Application.dataPath)?.FullName;
            if (string.IsNullOrEmpty(projectRoot))
            {
                throw new InvalidOperationException("Unity project root was not found.");
            }

            return Path.GetFullPath(Path.Combine(projectRoot, relativePath));
        }
    }

    public static class AssetValidationBatch
    {
        public static void Run()
        {
            var configPath =
                CommandLineValue("-harnessAssetValidationConfig")
                ?? AssetValidator.DefaultConfigPath;
            var outputPath = CommandLineValue("-harnessAssetValidationOutput");
            if (string.IsNullOrWhiteSpace(outputPath))
            {
                throw new ArgumentException(
                    "Provide -harnessAssetValidationOutput <path>.");
            }

            var report = AssetValidator.ValidateProject(configPath);
            var fullOutputPath = Path.IsPathRooted(outputPath)
                ? outputPath
                : Path.Combine(
                    Directory.GetParent(Application.dataPath)?.FullName
                        ?? string.Empty,
                    outputPath);
            var directory = Path.GetDirectoryName(fullOutputPath);
            if (!string.IsNullOrEmpty(directory))
            {
                Directory.CreateDirectory(directory);
            }

            File.WriteAllText(
                fullOutputPath,
                JsonUtility.ToJson(report, true) + "\n",
                new UTF8Encoding(false));
            Debug.Log(
                $"Unity Codex Harness asset validation: {report.status}; "
                + $"errors={report.errors.Count}; warnings={report.warnings.Count}");
            EditorApplication.Exit(report.status == "PASS" ? 0 : 1);
        }

        private static string CommandLineValue(string name)
        {
            var arguments = Environment.GetCommandLineArgs();
            for (var index = 0; index < arguments.Length - 1; index++)
            {
                if (arguments[index] == name)
                {
                    return arguments[index + 1];
                }
            }

            return null;
        }
    }
}
