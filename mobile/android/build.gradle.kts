allprojects {
    repositories {
        google()
        mavenCentral()
    }
}

val newBuildDir: Directory =
    rootProject.layout.buildDirectory
        .dir("../../build")
        .get()
rootProject.layout.buildDirectory.value(newBuildDir)

subprojects {
    val newSubprojectBuildDir: Directory = newBuildDir.dir(project.name)
    project.layout.buildDirectory.value(newSubprojectBuildDir)
}
subprojects {
    project.evaluationDependsOn(":app")
}

// stripe_android pulls an optional issuing dependency whose release lint
// artifact is no longer published. The app does not use issuing/provisioning;
// skip only that plugin lint task so regular Stripe PaymentSheet stays enabled.
subprojects {
    if (name == "stripe_android") {
        tasks.matching { it.name == "lintVitalAnalyzeRelease" }.configureEach {
            enabled = false
        }
    }
}

tasks.register<Delete>("clean") {
    delete(rootProject.layout.buildDirectory)
}
