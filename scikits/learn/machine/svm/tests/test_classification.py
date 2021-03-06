from itertools import izip
from unittest import TestCase
from numpy.testing import assert_array_equal, assert_array_almost_equal
import numpy as N

from ..classification import CClassificationModel, NuClassificationModel
from ..dataset import ClassificationDataSet, TestDataSet
from ..kernel import Linear, Polynomial, RBF, Custom
from ..predict import PythonPredictor, Predictor

class TestClassification(TestCase):
    def test_basics(self):
        kernel = Linear()
        # C-SVC
        ModelType = CClassificationModel
        ModelType(kernel)
        ModelType(kernel, cost=1.0)
        weights = [(2, 10.0), (1, 20.0), (0, 30.0)]
        ModelType(kernel, weights=weights)
        ModelType(kernel, 1.0, weights)
        ModelType(kernel, cost=1.0, weights=weights)
        # nu-SVC
        ModelType = NuClassificationModel
        ModelType(kernel)
        ModelType(kernel, nu=0.5)
        ModelType(kernel, weights=weights)
        ModelType(kernel, 0.5, weights)

    def _make_basic_datasets(self):
        labels = [0, 1, 1, 2]
        x = [N.array([0, 0]),
             N.array([0, 1]),
             N.array([1, 0]),
             N.array([1, 1])]
        traindata = ClassificationDataSet(labels, x)
        testdata = TestDataSet(x)
        return traindata, testdata

    def test_c_basics(self):
        traindata, testdata = self._make_basic_datasets()
        kernel = RBF(traindata.gamma)
        model = CClassificationModel(kernel)
        results = model.fit(traindata)
        p = results.predict(testdata)
        assert_array_equal(p, [1, 1, 1, 1])
        results.predict_values(testdata)

    def _make_basic_kernels(self, gamma):
        kernels = [
            Linear(),
            Polynomial(3, gamma, 0.0),
            RBF(gamma)
            ]
        return kernels

    def _classify_basic(self, ModelType,
                        modelargs, expected_rhos, expected_ps):
        traindata, testdata = self._make_basic_datasets()
        kernels = self._make_basic_kernels(traindata.gamma)
        for kernel, expected_rho, expected_p in \
                zip(kernels, expected_rhos, expected_ps):
            args = (kernel,) + modelargs
            model = ModelType(*args)
            results = model.fit(traindata)
            self.assertEqual(results.labels, [0, 1, 2])
            # decimal=4 due to compiler-dependent variations in rho
            assert_array_almost_equal(results.rho, expected_rho, decimal=4)
            p = N.array(results.predict(testdata))
            assert_array_equal(p, expected_p)

    def test_c_more(self):
        cost = 10.0
        weights = [(1, 10.0)]
        modelargs = cost, weights
        expected_rhos = [[-0.999349, -1.0, -3.0],
                         [0.375, -1.0, -1.153547],
                         [0.671181, 0.0, -0.671133]]
        expected_ps = [[0, 1, 1, 2], [1, 1, 1, 2], [0, 1, 1, 2]]
        self._classify_basic(CClassificationModel,
                             modelargs, expected_rhos, expected_ps)

    def test_c_probability(self):
        traindata, testdata = self._make_basic_datasets()
        nu = 0.5
        cost = 10.0
        weights = [(1, 10.0)]
        kernels = self._make_basic_kernels(traindata.gamma)
        models = [
            (CClassificationModel, (cost, weights)),
            (NuClassificationModel, (nu, weights))
            ]
        for ModelType, modelargs in models:
            for kernel in kernels:
                args = (kernel,) + modelargs
                kwargs = {'probability' : True}
                model = ModelType(*args, **kwargs)
                results = model.fit(traindata)
                results.predict_probability(testdata)

    def test_cross_validate(self):
        labels = ([-1] * 50) + ([1] * 50)
        x = N.random.randn(len(labels), 10)
        traindata = ClassificationDataSet(labels, x)
        kernel = Linear()
        model = CClassificationModel(kernel)
        nr_fold = 10
        pcorr = model.cross_validate(traindata, nr_fold)
        # XXX check cross-validation with and without probability
        # output enabled

    def test_nu_basics(self):
        traindata, testdata = self._make_basic_datasets()
        kernel = RBF(traindata.gamma)
        model = NuClassificationModel(kernel)
        results = model.fit(traindata)
        p = results.predict(testdata)
        assert_array_equal(p, [0, 1, 1, 2])
        v = results.predict_values(testdata)

    def test_nu_more(self):
        nu = 0.5
        weights = [(1, 10.0)]
        modelargs = nu, weights
        expected_rhos = [[-1.0, -1.0, -3.0],
                         [-1.0, -1.0, -1.15384846],
                         [0.6712142, 0.0, -0.6712142]]
        expected_ps = [[0, 1, 1, 2]] * 3
        self._classify_basic(NuClassificationModel,
                             modelargs, expected_rhos, expected_ps)

    def _make_datasets(self):
        labels1 = N.random.random_integers(0, 2, 100)
        x1 = N.random.randn(len(labels1), 10)
        labels2 = N.random.random_integers(0, 2, 10)
        x2 = N.random.randn(len(labels2), x1.shape[1])
        trndata1 = ClassificationDataSet(labels1, x1)
        trndata2 = ClassificationDataSet(labels2, x2)
        reflabels = N.concatenate([labels1, labels2])
        refx = N.vstack([x1, x2])
        trndata = ClassificationDataSet(reflabels, refx)
        testdata = TestDataSet(refx)
        return trndata, testdata, trndata1, trndata2

    def _make_kernels(self):
        def kernelf(x, y, dot):
            return dot(x, y)
        def kernelg(x, y, dot):
            return -dot(x, y)
        kernels = [Linear()]
        #kernels += [RBF(gamma)
        #            for gamma in [-0.1, 0.2, 0.3]]
        #kernels += [Polynomial(degree, gamma, coef0)
        #            for degree, gamma, coef0 in
        #            [(1, 0.1, 0.0), (2, -0.2, 1.3), (3, 0.3, -0.3)]]
        #kernels += [Sigmoid(gamma, coef0)
        #            for gamma, coef0 in [(0.2, -0.5), (-0.5, 1.5)]]
        #kernels += [Custom(f) for f in [kernelf, kernelg]]
        return kernels

    def test_all(self):
        trndata, testdata, trndata1, trndata2 = self._make_datasets()
        kernels = self._make_kernels()
        weights = [(0, 2.0), (1, 5.0), (2, 3.0)]
        for kernel in kernels:
            pctrndata1 = trndata1.precompute(kernel)
            pctrndata = pctrndata1.combine(trndata2)
            models = [
                CClassificationModel(kernel, 2.0, weights, True),
                NuClassificationModel(kernel, 0.3, weights, True)
                ]
            fitargs = []
            # Custom needs a precomputed dataset
            if not isinstance(kernel, Custom):
                fitargs += [
                    (trndata, Predictor),
                    #(trndata, PythonPredictor),
                    ]
            fitargs += [
                (pctrndata, Predictor),
                #(pctrndata, PythonPredictor)
                ]

            for model in models:
                refresults = model.fit(*fitargs[0])
                refrho = refresults.rho
                refp = refresults.predict(testdata)
                refv = refresults.predict_values(testdata)
                refpp = refresults.predict_probability(testdata)
                for args in fitargs[1:]:
                    results = model.fit(*args)
                    assert_array_almost_equal(results.rho, refrho)
                    p = results.predict(testdata)
                    assert_array_almost_equal(refp, p)
                    v = results.predict_values(testdata)
                    for v, refv in zip(v, refv):
                        for key, value in refv.iteritems():
                            self.assertAlmostEqual(v[key], value)
                    try:
                        pp = results.predict_probability(testdata)
                        # XXX there are slight differences between
                        # precomputed and normal kernels here
                        #for (lbl, p), (reflbl, refp) in zip(pp, refpp):
                        #    self.assertEqual(lbl, reflbl)
                        #    assert_array_almost_equal(p, refp)
                    except NotImplementedError:
                        self.assert_(fitargs[-1] is PythonPredictor)

    def test_python_predict(self):
        traindata, testdata = self._make_basic_datasets()
        kernel = Linear()
        cost = 10.0
        weights = [(1, 10.0)]
        model = CClassificationModel(kernel, cost, weights)

        refresults = model.fit(traindata)
        results = model.fit(traindata, PythonPredictor)

        refv = refresults.predict_values(testdata)
        v = results.predict_values(testdata)
        self.assertEqual(len(refv), len(v))
        for pred, refpred in zip(v, refv):
            for key, value in refpred.iteritems():
                assert_array_almost_equal(value, pred[key])

        refp = refresults.predict(testdata)
        p = results.predict(testdata)
        assert_array_equal(p, refp)

    def xtest_compact(self):
        traindata, testdata = self._make_basic_datasets()
        kernel = Linear()
        cost = 10.0
        weights = [(1, 10.0)]
        model = CClassificationModel(kernel, cost, weights)
        results = model.fit(traindata, PythonPredictor)
        refvs = results.predict_values(testdata)
        results.compact()
        vs = results.predict_values(testdata)
        for refv, v in zip(refvs, vs):
            for key, value in refv.iteritems():
                self.assertEqual(value, v[key])

    def _make_compact_test_datasets(self):
        x = N.random.randn(150, 3)
        labels = N.random.random_integers(1, 5, x.shape[0])
        traindata = ClassificationDataSet(labels, x)
        xdim, ydim, zdim = 4, 4, x.shape[1]
        img = N.random.randn(xdim, ydim, zdim)
        testdata1 = TestDataSet(img.reshape(xdim*ydim, zdim))
        testdata2 = TestDataSet(list(img.reshape(xdim*ydim, zdim)))
        return traindata, testdata1, testdata2

    def test_compact_predict_values(self):
        def compare_predict_values(vx, vy):
            for pred1, pred2 in izip(vx, vy):
                for labels, x in pred1.iteritems():
                    self.assert_(labels in pred2)
                    self.assertAlmostEqual(x, pred2[labels])
        traindata, testdata1, testdata2 = \
            self._make_compact_test_datasets()
        kernel = Linear()
        model = CClassificationModel(kernel)
        refresults = model.fit(traindata)
        refv1 = refresults.predict_values(testdata1)
        refv2 = refresults.predict_values(testdata2)
        results = model.fit(traindata, PythonPredictor)
        v11 = results.predict_values(testdata1)
        v12 = results.predict_values(testdata2)
        results.compact()
        v21 = results.predict_values(testdata1)
        v22 = results.predict_values(testdata2)
        compare_predict_values(refv1, refv2)
        compare_predict_values(refv1, v11)
        compare_predict_values(refv1, v12)
        compare_predict_values(refv1, v21)
        # XXX this test fails
        #compare_predict_values(refv1, v22)

    def test_compact_predict(self):
        traindata, testdata1, testdata2 = \
            self._make_compact_test_datasets()
        kernel = Linear()
        model = CClassificationModel(kernel)
        refresults = model.fit(traindata)
        refp1 = refresults.predict(testdata1)
        refp2 = refresults.predict(testdata2)
        results = model.fit(traindata, PythonPredictor)
        p11 = results.predict(testdata1)
        p12 = results.predict(testdata2)
        results.compact()
        p21 = results.predict(testdata1)
        p22 = results.predict(testdata2)
        self.assertEqual(refp1, refp2)
        self.assertEqual(refp1, p11)
        self.assertEqual(refp1, p12)
        # XXX these tests fail
        #self.assertEqual(refp1, p21)
        #self.assertEqual(refp1, p22)

    def test_no_support_vectors(self):
        x = N.array([[10.0, 20.0]])
        labels = [1]
        traindata = ClassificationDataSet(labels, x)
        kernel = Linear()
        model = CClassificationModel(kernel)
        testdata = TestDataSet(x)
        self.assertRaises(ValueError, model.fit, traindata)
