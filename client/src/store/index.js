import Vuex from 'vuex';
import VuexPersistence from 'vuex-persist';

import {
  postSignup, postLogin, getGroupNames, getGroup, patchScores, getScoreBoard, postComputePoints
} from '@/api';
import isValidJwt from '@/utils';

const stateObject = {
  userName: '',
  jwt: '',
};

const actions = {
  getGroup(context, { groupName }) {
    return getGroup(groupName, context.state.jwt);
  },
  patchScores(context, { matchId, matchResource, type }) {
    return patchScores(matchId, matchResource, type, context.state.jwt);
  },
  getScoreBoard(context) {
    return getScoreBoard(context.state.jwt);
  },
  getGroupNames(context) {
    return getGroupNames(context.state.jwt);
  },
  login(context, userData) {
    return postLogin(userData);
  },
  signup(context, userData) {
    return postSignup(userData);
  },
  computePoints(context) {
    return postComputePoints(context.state.jwt);
  },
};

const mutations = {
  setUserName(state, payload) {
    state.userName = payload.userName;
  },
  setJwtToken(state, payload) {
    state.jwt = payload.jwt;
  },
  eraseJwtToken(state) {
    state.jwt = 'deleted';
    state.userName = '';
  },
};

const getters = {
  isAuthenticated(state) {
    return state.jwt && isValidJwt(state.jwt);
  },
  getUserName(state) {
    return state.userName;
  },
};

const vuexPersist = new VuexPersistence({
  key: 'myStorage',
  reducer: (state) => state,
});

const store = new Vuex.Store({
  stateObject,
  actions,
  mutations,
  getters,
  plugins: [vuexPersist.plugin],
});

export default store;
