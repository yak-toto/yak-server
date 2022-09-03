// api/index.js

import axios from 'axios';

const URL = process.env.NODE_ENV === 'production' ? 'https://yak-toto.com' : 'http://127.0.0.1:5000';
const GLOBAL_ENDPOINT = 'api';
const VERSION = 'v1';

// ------------------------------
// Auth interface
// ------------------------------

export function postSignup(userData) {
  return axios.post(`${URL}/${GLOBAL_ENDPOINT}/${VERSION}/signup`, userData);
}

export function postLogin(userData) {
  return axios.post(`${URL}/${GLOBAL_ENDPOINT}/${VERSION}/login`, userData);
}

// ------------------------------
// Group interface
// ------------------------------

export function getGroupNames(jwt) {
  return axios.get(`${URL}/${GLOBAL_ENDPOINT}/${VERSION}/groups/names`, { headers: { Authorization: `Bearer: ${jwt}` } });
}

export function getGroup(groupName, jwt) {
  return axios.get(`${URL}/${GLOBAL_ENDPOINT}/${VERSION}/bets/groups/${groupName}`, { headers: { Authorization: `Bearer: ${jwt}` } });
}

export function patchScores(matchId, matchResource, jwt) {
  return axios.patch(`${URL}/${GLOBAL_ENDPOINT}/${VERSION}/bets/scores/${matchId}`, matchResource, { headers: { Authorization: `Bearer: ${jwt}` } });
}

// ------------------------------
// Result interface
// ------------------------------

export function getScoreBoard(jwt) {
  return axios.get(`${URL}/${GLOBAL_ENDPOINT}/${VERSION}/score_board`, { headers: { Authorization: `Bearer: ${jwt}` } });
}

// ------------------------------
// Admin interface
// ------------------------------

export function postComputePoints(jwt) {
  return axios.post(`${URL}/${GLOBAL_ENDPOINT}/${VERSION}/compute_points`, null, { headers: { Authorization: `Bearer: ${jwt}` } })
}
